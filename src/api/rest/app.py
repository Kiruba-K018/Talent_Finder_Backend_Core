import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handler import setup_error_handlers
from src.api.middleware.logging import LoggingMiddleware
from src.api.rest.routes.auth.auth import auth_router
from src.api.rest.routes.auth.role_permission import role_permission_router
from src.api.rest.routes.auth.users import users_router
from src.api.rest.routes.job_post.job_post import job_post_router
from src.api.rest.routes.job_post.shortlist import candidate_shortlist_router
from src.api.rest.routes.organization.organization import organization_router
from src.api.rest.routes.source_runs.config_sourcing import sourcing_config_router
from src.api.rest.routes.sourced_candidates.sourced_candidates import (
    sourced_candidates_router,
)
from src.api.rest.routes.source_runs.source_runs import source_run_router
from src.core.utils.background_task_manager import (
    get_background_task_manager,
    shutdown_background_task_manager,
)
from src.data.clients.pgvector_client import close_pgvector, init_pgvector
from src.data.clients.mongodb_client import close_mongo_connection, connect_to_mongo
from src.data.clients.postgres_client import close_engine, init_pg_engine, create_tables
from src.data.migrations.pgvector_migrations import run_migrations
from src.utils.seed_database import seed_database_from_sql
from src.utils.seed_resume import seed

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3001,http://localhost:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Starting application lifespan ===")

        try:
            print("=== STARTING: Initializing PostgreSQL engine ===")
            logger.info("Initializing PostgreSQL engine...")
            await init_pg_engine()
            print("=== SUCCESS: PostgreSQL engine initialized ===")
            logger.info("PostgreSQL engine initialized")

            print("=== STARTING: Creating database tables ===")
            logger.info("Creating database tables...")
            await create_tables()
            print("=== SUCCESS: Database tables created ===")
            logger.info("Database tables created")

            print("=== STARTING: Seeding database ===")
            logger.info("Seeding database with initial data...")
            # Import engine after init_pg_engine() has been called
            import src.data.clients.postgres_client as pg_client
            if pg_client.engine is not None:
                print(f"Engine found: {pg_client.engine}")
                await seed_database_from_sql(pg_client.engine)
                print("=== SUCCESS: Database seeding completed ===")
                logger.info("Database seeding completed")
            else:
                print("=== WARNING: PostgreSQL engine is None, skipping seeding ===")
                logger.warning("PostgreSQL engine not initialized, skipping database seeding")
        except Exception as e:
            print(f"=== ERROR in PostgreSQL initialization: {e} ===")
            logger.warning(f"PostgreSQL initialization failed (app will continue): {e}")

        try:
            logger.info("Initializing pgvector connection pool...")
            await init_pgvector()
            logger.info("pgvector connection pool initialized")

            logger.info("Running pgvector migrations...")
            await run_migrations()
            logger.info("pgvector migrations completed")
        except Exception as e:
            logger.warning(f"pgvector initialization failed (app will continue): {e}")

        try:
            logger.info("Connecting to MongoDB...")
            await connect_to_mongo()
            logger.info("MongoDB connected")
        except Exception as e:
            logger.warning(f"MongoDB initialization failed (app will continue): {e}")

        try:
            print("=== STARTING: Seeding resume data ===")
            logger.info("Seeding resume data...")
            
            # await seed()
            print("=== SUCCESS: Resume data seeding completed ===")
            logger.info("Resume data seeding completed")
        except Exception as e:
            print(f"=== ERROR in resume seeding: {e} ===")
            logger.warning(f"Resume data seeding failed (app will continue): {e}")

        try:
            logger.info("Initializing Background Task Manager...")
            get_background_task_manager(max_workers=20)
            logger.info("Background Task Manager initialized")
        except Exception as e:
            logger.warning(f"Background Task Manager initialization failed: {e}")

        logger.info("=== Application startup complete (with warnings if any) ===")
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}", exc_info=True)
        raise

    yield

    try:
        logger.info("=== Starting application shutdown ===")
        await close_engine()
        await close_mongo_connection()
        await close_pgvector()
        shutdown_background_task_manager(wait=True)
        logger.info("=== Application shutdown complete ===")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)


app = FastAPI(
    title="Talent Finder API",
    description="A resume Sourcing and Shortlisting application",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://talentfinder-frontend-717740758627.us-east1.run.app",
        "https://talentfinder-backend-sourcing-717740758627.us-east1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_error_handlers(app)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(role_permission_router)
app.include_router(organization_router)
app.include_router(job_post_router)
app.include_router(candidate_shortlist_router)
app.include_router(sourcing_config_router)
app.include_router(sourced_candidates_router)
app.include_router(source_run_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run startup probe."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
