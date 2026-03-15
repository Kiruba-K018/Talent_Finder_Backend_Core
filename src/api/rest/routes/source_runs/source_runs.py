import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.postgres_client import get_db
from src.core.services.source_run.source_run_services import (create_source_run_record_service, 
fetch_all_source_runs_service, fetch_one_source_run_service)


source_run_router = APIRouter(prefix="/api/v1/source-runs", tags=["Source Runs"])

@source_run_router.post("/", status_code=status.HTTP_200_OK)
async def create_source_run_record(config:dict, db: AsyncSession = Depends(get_db)):
    """Create a new source run record in the database."""
    try:
        await create_source_run_record_service(config, db)
        return {"message": "Source run record created", "config": config}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@source_run_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_source_runs(db: AsyncSession = Depends(get_db)):
    """Fetch all source run records from the database."""
    return await fetch_all_source_runs_service(db)

@source_run_router.get("/{source_run_id}", status_code=status.HTTP_200_OK)
async def get_one_source_run(source_run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single source run record by its ID."""
    return await fetch_one_source_run_service(db, source_run_id)