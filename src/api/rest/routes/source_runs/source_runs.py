import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.postgres_client import get_db
from src.core.services.source_run.source_run_services import (create_source_run_record_service, 
fetch_all_source_runs_service, fetch_one_source_run_service, delete_source_run_service)
from src.schemas.source_run_schema import (
    SourceRunResponse,
    SourceRunListResponse,
    SourceRunDetailResponse,
    SourceRunDeleteResponse,
)


source_run_router = APIRouter(prefix="/api/v1/source-runs", tags=["Source Runs"])

@source_run_router.post("/", status_code=status.HTTP_201_CREATED, response_model=SourceRunResponse)
async def create_source_run_record(config:dict, db: AsyncSession = Depends(get_db))-> SourceRunResponse:
    """Create a new source run record.
    
    Records a new execution of the sourcing configuration with results.
    
    Args:
        config: Dictionary containing sourcing configuration and results.
        db: Database session for source run creation.
    
    Returns:
        SourceRunResponse: Created source run with id and config.
    
    Raises:
        HTTPException: 500 for database or service errors.
    """
    try:
        result = await create_source_run_record_service(config, db)
        if isinstance(result, dict) and "source_run_id" in result:
            return SourceRunResponse(source_run_id=result["source_run_id"], config=config)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

@source_run_router.get("/", status_code=status.HTTP_200_OK, response_model=SourceRunListResponse)
async def get_all_source_runs(db: AsyncSession = Depends(get_db))-> SourceRunListResponse:
    """Retrieve all source run records.
    
    Returns complete history of all sourcing job executions.
    
    Args:
        db: Database session for source run queries.
    
    Returns:
        SourceRunListResponse: List of all source runs with details.
    """
    return await fetch_all_source_runs_service(db)

@source_run_router.get("/{source_run_id}", status_code=status.HTTP_200_OK, response_model=SourceRunDetailResponse)
async def get_one_source_run(source_run_id: uuid.UUID, db: AsyncSession = Depends(get_db))-> SourceRunDetailResponse:
    """Retrieve a specific source run by ID.
    
    Returns complete details of a specific sourcing job execution.
    
    Args:
        source_run_id: UUID of the source run.
        db: Database session for source run lookup.
    
    Returns:
        SourceRunDetailResponse: Detailed source run information.
    
    Raises:
        HTTPException: 404 if source run not found.
    """
    return await fetch_one_source_run_service(db, source_run_id)


@source_run_router.delete("/{source_run_id}", status_code=status.HTTP_200_OK, response_model=SourceRunDeleteResponse)
async def delete_source_run(source_run_id: uuid.UUID, db: AsyncSession = Depends(get_db))-> SourceRunDeleteResponse:
    """Delete a source run record.
    
    Removes a source run and associated candidate records from the system.
    
    Args:
        source_run_id: UUID of the source run to delete.
        db: Database session for deletion operation.
    
    Returns:
        SourceRunDeleteResponse: Confirmation message of deletion.
    
    Raises:
        HTTPException: 500 for database or service errors.
    """
    try:
        await delete_source_run_service(db, source_run_id)
        return SourceRunDeleteResponse(message=f"Source run {source_run_id} deleted successfully")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )