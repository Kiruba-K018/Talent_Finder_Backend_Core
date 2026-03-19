"""
PostgreSQL with pgvector client for vector embeddings.
Replaces ChromaDB with PostgreSQL + pgvector for vector similarity search.
Uses connection pooling for Cloud SQL optimization.
"""

import json
import logging
import warnings
from contextlib import asynccontextmanager
from typing import Any, Optional

import psycopg
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from src.config.settings import setting

logger = logging.getLogger(__name__)

# Suppress deprecation warning for AsyncConnectionPool constructor
# We're explicitly calling await _pool.open() as recommended
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*opening the async pool.*")

# Global connection pool
_pool: Optional[AsyncConnectionPool] = None


async def init_pgvector() -> None:
    """
    Initialize pgvector connection pool at app startup.
    Creates the pool and ensures database schema is initialized.
    
    For Cloud SQL: Uses reduced pool sizes to avoid connection exhaustion.
    """
    global _pool

    try:
        logger.info("Initializing pgvector connection pool...")
        
        # Get connection URL
        conn_url = setting.database_url
        logger.debug(f"Using PostgreSQL host: {setting.postgres_host}:{setting.postgres_port}/{setting.postgres_db}")
        
        # Convert SQLAlchemy format to psycopg3 format if needed
        if "postgresql+psycopg://" in conn_url:
            logger.warning("Converting SQLAlchemy connection URL format to psycopg3 format")
            conn_url = conn_url.replace("postgresql+psycopg://", "postgresql://")
            logger.debug(f"Converted URL format: {conn_url.split('@')[0]}@...")
        
        if not conn_url.startswith("postgresql://"):
            logger.error(f"Invalid connection URL format. Expected 'postgresql://' format, got: {conn_url[:30]}...")
            raise ValueError("Connection URL must use 'postgresql://' format for psycopg3")

        # Use reduced pool sizes for Cloud SQL to avoid connection exhaustion
        min_size = getattr(setting, 'postgres_pool_min_size', 1)
        max_size = setting.postgres_pool_size
        
        logger.info(f"Creating AsyncConnectionPool with min_size={min_size}, max_size={max_size}")
        logger.info("(Cloud SQL: Using reduced pool sizes to avoid connection exhaustion)")
        
        # Create async connection pool using psycopg3 format
        # Suppress constructor deprecation warning - we call await _pool.open() explicitly
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            _pool = AsyncConnectionPool(
                conninfo=conn_url,
                min_size=min_size,
                max_size=max_size,
                timeout=30,
            )

        # Open the pool
        logger.debug("Opening connection pool...")
        await _pool.open()
        logger.info(f"[OK] Connection pool opened successfully (min={min_size}, max={max_size})")

        # Initialize database schema
        await _initialize_schema()
        logger.info("[OK] pgvector schema initialized successfully")

    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize pgvector: {e}", exc_info=True)
        raise


async def _initialize_schema() -> None:
    """Create required tables and indexes if they don't exist."""
    async with get_db_connection() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        logger.debug("pgvector extension enabled")

        # Create embeddings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                collection_name TEXT NOT NULL,
                document TEXT NOT NULL,
                embedding vector(384) NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.debug("embeddings table created")

        # Create indexes for better query performance
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_embeddings_collection ON embeddings(collection_name)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_embeddings_metadata ON embeddings USING GIN(metadata)"
        )

        # Create IVFFLAT index for vector similarity search (cosine distance)
        # This index is optimized for similarity search operations
        try:
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            )
            logger.debug("IVFFLAT vector index created")
        except Exception as e:
            logger.warning(f"IVFFLAT index creation failed (might already exist): {e}")
            # Try with different settings if IVFFLAT fails
            try:
                await conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops)"
                )
            except Exception as e2:
                logger.warning(f"Could not create vector index: {e2}")

        await conn.commit()


@asynccontextmanager
async def get_db_connection() -> AsyncConnection:
    """
    Get a database connection from the pool.
    Important: In background tasks or separate event loops, the pool may not be
    initialized. This function checks and handles that case.
    Usage:
        async with get_db_connection() as conn:
            await conn.execute(...)
    """
    global _pool

    if not _pool:
        logger.warning("pgvector pool not initialized in this context, initializing now...")
        try:
            await init_pgvector()
        except Exception as e:
            logger.error(f"Failed to initialize pgvector pool: {e}")
            raise RuntimeError("pgvector connection pool not initialized. Call init_pgvector() first.")

    async with _pool.connection() as conn:
        yield conn


async def close_pgvector() -> None:
    """Close the connection pool at app shutdown."""
    global _pool

    if _pool:
        await _pool.close()
        _pool = None
        logger.info("pgvector connection pool closed")




class Collection:
    """
    Represents a pgvector collection, mimicking ChromaDB's Collection interface.
    This provides a consistent API for working with embeddings.
    """

    def __init__(self, name: str):
        self.name = name

    async def add(
        self,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict],
        embeddings: Optional[list[list[float]]] = None,
    ) -> None:
        """
        Add documents to the collection.
        
        Args:
            documents: List of document texts to embed
            ids: List of document IDs (must match document count)
            metadatas: List of metadata dicts for each document
            embeddings: Optional pre-computed embeddings (for batch operations)
        """
        if not documents:
            return

        if len(documents) != len(ids) or len(documents) != len(metadatas):
            raise ValueError(
                f"documents, ids, and metadatas must have the same length. "
                f"Got {len(documents)}, {len(ids)}, {len(metadatas)}"
            )

        # Get embeddings if not provided
        if embeddings is None:
            embeddings = await get_embeddings(documents)

        async with get_db_connection() as conn:
            # Use UPSERT to handle duplicates gracefully
            query = """
                INSERT INTO embeddings (id, collection_name, document, embedding, metadata)
                VALUES %s
                ON CONFLICT (id) DO UPDATE SET
                    document = EXCLUDED.document,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """

            # Prepare values
            values = [
                (
                    ids[i],
                    self.name,
                    documents[i],
                    embeddings[i],
                    json.dumps(metadatas[i]) if metadatas[i] else "{}",
                )
                for i in range(len(documents))
            ]

            # Use executemany for batch insert
            async with conn.cursor() as cur:
                try:
                    # Convert to format suitable for psycopg3
                    for doc_id, collection, doc, emb, meta in values:
                        await cur.execute(
                            """
                            INSERT INTO embeddings (id, collection_name, document, embedding, metadata)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                document = EXCLUDED.document,
                                embedding = EXCLUDED.embedding,
                                metadata = EXCLUDED.metadata,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            (doc_id, collection, doc, emb, meta),
                        )
                    await conn.commit()
                    logger.debug(f"Added {len(values)} documents to collection '{self.name}'")
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Failed to add documents to collection '{self.name}': {e}")
                    raise

    async def get(self, ids: list[str]) -> dict:
        """
        Retrieve documents by IDs.
        
        Returns: Dictionary with keys 'ids', 'documents', 'embeddings', 'metadatas'
        """
        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, document, embedding, metadata
                    FROM embeddings
                    WHERE id = ANY(%s) AND collection_name = %s
                    ORDER BY id
                    """,
                    (ids, self.name),
                )

                rows = await cur.fetchall()
                # Manually convert to dict using cursor.description
                col_names = [desc[0] for desc in cur.description]
                rows_as_dicts = [dict(zip(col_names, row)) for row in rows]

                return {
                    "ids": [row["id"] for row in rows_as_dicts],
                    "documents": [row["document"] for row in rows_as_dicts],
                    "embeddings": [row["embedding"] for row in rows_as_dicts],
                    "metadatas": [row["metadata"] for row in rows_as_dicts],
                }

    async def update(
        self,
        ids: list[str],
        documents: Optional[list[str]] = None,
        metadatas: Optional[list[dict]] = None,
        embeddings: Optional[list[list[float]]] = None,
    ) -> None:
        """
        Update documents in the collection.
        
        Args:
            ids: List of document IDs to update
            documents: New document texts (regenerates embeddings if provided)
            metadatas: New metadata dicts
            embeddings: Pre-computed embeddings (optional)
        """
        if not ids:
            return

        # Regenerate embeddings if documents are updated
        if documents and embeddings is None:
            embeddings = await get_embeddings(documents)

        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                try:
                    for i, doc_id in enumerate(ids):
                        # Build the update query dynamically
                        updates = ["updated_at = CURRENT_TIMESTAMP"]
                        params = []

                        if documents:
                            updates.append("document = %s")
                            params.append(documents[i])

                        if embeddings:
                            updates.append("embedding = %s")
                            params.append(embeddings[i])

                        if metadatas:
                            updates.append("metadata = %s")
                            params.append(json.dumps(metadatas[i]) if metadatas[i] else "{}")

                        # Add WHERE clause parameters at the end
                        params.append(doc_id)
                        params.append(self.name)

                        update_clause = ", ".join(updates)
                        query = f"""
                            UPDATE embeddings
                            SET {update_clause}
                            WHERE id = %s AND collection_name = %s
                        """

                        await cur.execute(query, params)

                    await conn.commit()
                    logger.debug(f"Updated {len(ids)} documents in collection '{self.name}'")
                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        f"Failed to update documents in collection '{self.name}': {e}"
                    )
                    raise

    async def delete(self, ids: list[str]) -> None:
        """Delete documents from the collection by IDs."""
        if not ids:
            return

        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        """
                        DELETE FROM embeddings
                        WHERE id = ANY(%s) AND collection_name = %s
                        """,
                        (ids, self.name),
                    )
                    await conn.commit()
                    logger.debug(f"Deleted {len(ids)} documents from collection '{self.name}'")
                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        f"Failed to delete documents from collection '{self.name}': {e}"
                    )
                    raise

    async def query(
        self,
        query_embeddings: list[list[float]] = None,
        query_texts: list[str] = None,
        n_results: int = 10,
        filter_metadata: Optional[dict] = None,
    ) -> dict:
        """
        Perform similarity search on the collection.
        
        Args:
            query_embeddings: Pre-computed query embeddings (use OR query_texts)
            query_texts: Query texts to embed (use OR query_embeddings)
            n_results: Number of results to return
            filter_metadata: Optional metadata filter (as JSONB query)
        
        Returns: Dictionary with 'ids', 'documents', 'distances', 'embeddings', 'metadatas'
        """
        if query_embeddings is None and query_texts is None:
            raise ValueError("Either query_embeddings or query_texts must be provided")

        # Generate embeddings from texts if needed
        if query_embeddings is None:
            query_embeddings = await get_embeddings(query_texts)

        results = {
            "ids": [],
            "documents": [],
            "distances": [],
            "embeddings": [],
            "metadatas": [],
        }

        async with get_db_connection() as conn:
            async with conn.cursor() as cur:
                for query_emb in query_embeddings:
                    
                    where_clause = "WHERE collection_name = %s"
                    # Format embedding as PostgreSQL array string
                    embedding_str = "[" + ",".join(str(x) for x in query_emb) + "]"
                    params = [embedding_str, self.name]

                    # Add optional metadata filter
                    if filter_metadata:
                        where_clause += " AND metadata @> %s::jsonb"
                        params.append(json.dumps(filter_metadata))

                    query = f"""
                        SELECT 
                            id, 
                            document, 
                            embedding, 
                            metadata,
                            (embedding <=> %s::vector) AS distance
                        FROM embeddings
                        {where_clause}
                        ORDER BY distance ASC
                        LIMIT %s
                    """
                    params.append(n_results)

                    await cur.execute(query, tuple(params))
                    rows = await cur.fetchall()
                    # Manually convert to dict using cursor.description
                    col_names = [desc[0] for desc in cur.description]
                    rows_as_dicts = [dict(zip(col_names, row)) for row in rows]

                    for row in rows_as_dicts:
                        results["ids"].append(row["id"])
                        results["documents"].append(row["document"])
                        results["distances"].append(float(row["distance"]))
                        results["embeddings"].append(row["embedding"])
                        results["metadatas"].append(row["metadata"])

        return results


def dict_row(cursor, row):
    """Row factory for converting rows to dicts (psycopg3 async format)."""
    cols = [desc[0] for desc in cursor.description]
    return {col: val for col, val in zip(cols, row)}


# ============================================================================
# Convenience Functions (Chroma-compatible API)
# ============================================================================


async def get_or_create_collection(name: str) -> Collection:
    """Get or create a collection (no-op for PostgreSQL, just returns Collection object)."""
    logger.debug(f"Getting collection '{name}'")
    return Collection(name)


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for texts using the configured model.
    
    Uses sentence-transformers "all-MiniLM-L6-v2" model (384 dimensions).
    This matches the ChromaDB default model for consistency.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error(
            "sentence-transformers not installed. Install with: pip install sentence-transformers"
        )
        raise

    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embeddings = model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


async def normalize_embeddings(embeddings: list[list[float]]) -> list[list[float]]:
    """
    Normalize embeddings for cosine similarity.
    pgvector handles normalization internally for cosine distance,
    but this is provided for explicit control if needed.
    """
    import numpy as np

    embeddings_array = np.array(embeddings)
    norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    normalized = embeddings_array / (norms + 1e-8)
    return normalized.tolist()
