import logging
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config.settings import setting




logger = logging.getLogger(__name__)



# Use DB_URL if provided (for Cloud Run with Cloud SQL proxy), otherwise construct from individual settings
if setting.db_url:
    # Convert from SQLAlchemy format to psycopg format if needed
    database_url = setting.db_url
    if "postgresql+psycopg://" in database_url:
        pass  # Already in correct format
    elif "postgresql://" in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://")
else:
    # Construct from individual settings (for local development)
    postgres_host = setting.postgres_host
    postgres_port = setting.postgres_port
    postgres_db = setting.postgres_db
    postgres_user = setting.postgres_user
    postgres_password = setting.postgres_password
    
    # URL-encode password to handle special characters
    encoded_password = quote(postgres_password, safe="")
    database_url = f"postgresql+psycopg://{postgres_user}:{encoded_password}@{postgres_host}:{postgres_port}/{postgres_db}"

DATABASE_URL = database_url
Base = declarative_base()

# Global engine and session factory - initialized on first use
engine = None
SessionLocal = None


async def init_pg_engine(test_query: str = "SELECT 1") -> None:
    """Initialize the PostgreSQL engine with proper connection args."""
    print(f"Initializing PostgreSQL engine with URL: {DATABASE_URL}")
    global engine, SessionLocal

    if engine is not None:
        logger.debug("Engine already initialized, skipping re-initialization")
        return

    try:
        logger.info(f"Initializing PostgreSQL engine: {DATABASE_URL.split('@')[0]}@***")

        # Create engine with reduced timeout for Cloud Run
        connect_args = {
            "sslmode": setting.postgres_ssl_mode,
            "connect_timeout": 5,  # Reduced from 10 to 5 seconds
        }

        engine = create_async_engine(
            DATABASE_URL,
            future=True,
            pool_size=2,
            max_overflow=1,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

        # Test the connection with shorter timeout
        try:
            async with engine.connect() as conn:
                await conn.execute(text(test_query))
            logger.info(
                f"Database connection successful with SSL mode: {setting.postgres_ssl_mode}"
            )
        except Exception as test_err:
            logger.warning(f"Database connection test failed: {test_err} - engine created anyway")


        # Create session factory
        SessionLocal = async_sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("SessionLocal factory created successfully")

    except Exception as exc:
        logger.warning(f"Initial DB connection attempt failed: {exc}")

        # If SSL mode is 'prefer' and connection failed, try a non-SSL fallback
        if setting.postgres_ssl_mode and setting.postgres_ssl_mode.lower() == "prefer":
            logger.info("POSTGRES_SSL_MODE=prefer — attempting fallback without SSL")
            try:
                fallback_connect_args = {
                    "sslmode": "disable",
                    "connect_timeout": 5,  # Reduced from 10 to 5 seconds
                }

                fallback_engine = create_async_engine(
                    DATABASE_URL,
                    future=True,
                    pool_size=2,
                    max_overflow=1,
                    pool_recycle=1800,
                    pool_pre_ping=True,
                    connect_args=fallback_connect_args,
                )

                async with fallback_engine.connect() as conn:
                    await conn.execute(text(test_query))

                engine = fallback_engine
                SessionLocal = async_sessionmaker(
                    bind=engine, class_=AsyncSession, expire_on_commit=False
                )
                logger.info("Fallback non-SSL connection succeeded")
                return

            except Exception as exc2:
                logger.warning(f"Fallback non-SSL connection failed: {exc2} - engine created anyway")
                engine = fallback_engine
                SessionLocal = async_sessionmaker(
                    bind=fallback_engine, class_=AsyncSession, expire_on_commit=False
                )
                return

        # Otherwise re-raise the original error so startup fails visibly
        engine = None
        SessionLocal = None
        raise


async def create_tables():
    """Create all tables defined in the ORM models."""
    # Import models here (inside function) to avoid circular imports
    # These imports register the models with Base.metadata
    from src.data.models.postgres import (
        auth_models,
        job_post_models,
        jobs_shortlist_models,
        source_run_models,
        sourcing_config_models,
    )

    global engine

    if engine is None:
        logger.error("Engine not initialized. Call init_pg_engine() first.")
        return

    try:
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}", exc_info=True)
        raise


async def close_engine():
    """Close the PostgreSQL engine and dispose of connections."""
    global engine
    if engine:
        logger.info("Closing PostgreSQL engine...")
        await engine.dispose()
        engine = None
        logger.info("PostgreSQL engine closed")


def get_session_factory():
    """Get or initialize the SessionLocal factory."""
    global engine, SessionLocal

    if engine is None or SessionLocal is None:
        raise RuntimeError("Engine not initialized. Call init_pg_engine() first.")

    return SessionLocal


async def get_db():
    """
    Dependency for getting a database session.
    Usage: async with get_db() as db: ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
