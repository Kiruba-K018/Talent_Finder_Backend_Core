import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from src.data.clients.chroma_client import close_chroma, init_chroma
from src.data.clients.mongodb_client import close_mongo_connection, connect_to_mongo
from src.data.clients.postgres_client import close_engine, init_pg_engine, create_tables

ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3001,http://localhost:3000"
).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Starting application lifespan ===")

        logger.info("Initializing PostgreSQL engine...")
        await init_pg_engine()
        logger.info("PostgreSQL engine initialized")

        logger.info("Creating database tables...")
        await create_tables()
        logger.info("Database tables created")

        logger.info("Connecting to MongoDB...")
        await connect_to_mongo()
        logger.info("MongoDB connected")

        logger.info("Initializing Chroma...")
        await init_chroma()
        logger.info("Chroma initialized")

        logger.info("Initializing Background Task Manager...")
        get_background_task_manager(max_workers=20)
        logger.info("Background Task Manager initialized")

        logger.info("=== Application startup complete ===")
    except Exception as e:
        logger.error(f"Failed during application startup: {e}", exc_info=True)
        raise

    yield

    try:
        logger.info("=== Starting application shutdown ===")
        await close_engine()
        await close_mongo_connection()
        await close_chroma()
        shutdown_background_task_manager(wait=True)
        logger.info("=== Application shutdown complete ===")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}", exc_info=True)


app = FastAPI(
    title="Talent Finder API",
    description="A resume Sourcing and Shortlisting application",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(role_permission_router)
app.include_router(organization_router)
app.include_router(job_post_router)
app.include_router(candidate_shortlist_router)
app.include_router(sourcing_config_router)
app.include_router(sourced_candidates_router)
app.include_router(source_run_router)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
