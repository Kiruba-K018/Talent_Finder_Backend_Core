import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config.settings import setting

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql+psycopg://{setting.postgres_user}:{setting.postgres_password}@{setting.postgres_host}:{setting.postgres_port}/{setting.postgres_db}"

Base = declarative_base()

# Global engine and session factory - initialized on first use
engine = None
SessionLocal = None


async def init_pg_engine(test_query: str = "SELECT 1") -> None:
    """Initialize the PostgreSQL engine with proper connection args."""
    global engine, SessionLocal

    if engine is not None:
        logger.debug("Engine already initialized, skipping re-initialization")
        return

    try:
        logger.info(f"Initializing PostgreSQL engine: {DATABASE_URL.split('@')[0]}@***")

        # Create engine with SSL mode preference handling
        connect_args = {
            "sslmode": setting.postgres_ssl_mode,
            "connect_timeout": 10,
        }

        engine = create_async_engine(
            DATABASE_URL,
            future=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

        # Test the connection
        async with engine.connect() as conn:
            await conn.execute(text(test_query))

        logger.info(
            f"Database connection successful with SSL mode: {setting.postgres_ssl_mode}"
        )

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
                    "connect_timeout": 10,
                }

                fallback_engine = create_async_engine(
                    DATABASE_URL,
                    future=True,
                    pool_size=10,
                    max_overflow=20,
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
                logger.error(f"Fallback non-SSL connection failed: {exc2}")
                engine = None
                SessionLocal = None
                raise

        # Otherwise re-raise the original error so startup fails visibly
        engine = None
        SessionLocal = None
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
