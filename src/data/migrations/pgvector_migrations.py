"""
Database migration scripts for pgvector setup.
Run migrations to initialize the database schema.
"""

import asyncio
import logging

from src.data.clients.pgvector_client import get_db_connection

logger = logging.getLogger(__name__)


async def run_migrations() -> None:
    """Run all database migrations."""
    logger.info("Starting database migrations...")

    try:
        await migrate_001_create_embeddings_table()
        logger.info("All migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


async def migrate_001_create_embeddings_table() -> None:
    """
    Migration 001: Create embeddings table and indexes.

    This migration creates:
    - embeddings table for storing vectors and metadata
    - Indexes for efficient querying
    - pgvector extension for vector operations
    """
    logger.info("Running migration 001: Create embeddings table...")

    async with get_db_connection() as conn:
        try:
            # Create pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.debug("pgvector extension created/verified")

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

            # Create collection index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_collection 
                ON embeddings(collection_name)
            """)
            logger.debug("Collection index created")

            # Create metadata JSONB index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_metadata 
                ON embeddings USING GIN(metadata)
            """)
            logger.debug("Metadata JSONB index created")

            # Create vector index for similarity search (IVFFLAT with cosine distance)
            # This index significantly speeds up similarity queries
            # lists = 100 is a good balance between build time and query quality
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embeddings_vector 
                ON embeddings USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100)
            """)
            logger.debug("Vector IVFFLAT index created")

            await conn.commit()
            logger.info("Migration 001 completed: embeddings table ready")

        except Exception as e:
            await conn.rollback()
            # Check if it's just index exists error (acceptable)
            if "already exists" in str(e).lower():
                logger.info("Migration 001: Objects already exist, continuing")
                await conn.commit()
            else:
                logger.error(f"Migration 001 failed: {e}")
                raise


async def check_schema() -> dict:
    """
    Check if the database schema is properly initialized.

    Returns:
        Dictionary with schema status information
    """
    schema_info = {
        "tables": {},
        "indexes": {},
        "extensions": [],
    }

    async with get_db_connection() as conn:
        # Check for pgvector extension
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            if await cur.fetchone():
                schema_info["extensions"].append("vector")

        # Check for embeddings table
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'embeddings'
                )
            """
            )
            table_exists = await cur.fetchone()
            schema_info["tables"]["embeddings"] = (
                bool(table_exists[0]) if table_exists else False
            )

        # Check for indexes
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'embeddings' AND indexname LIKE 'idx_%'
            """
            )
            rows = await cur.fetchall()
            schema_info["indexes"]["embeddings"] = [row[0] for row in rows]

    return schema_info


if __name__ == "__main__":
    # For manual migration execution
    asyncio.run(run_migrations())
