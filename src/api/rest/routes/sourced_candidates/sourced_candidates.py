from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter

from src.data.clients.mongodb_client import get_db
from src.core.services.sourced_candidates.sourced_candidate_service import (
    get_sourced_candidate_service,
    get_all_sourced_candidate_service,
    create_sourced_candidate_service
)   


sourced_candidates_router = APIRouter(
    prefix="/api/v1/sourced-candidates", tags=["Sourced Candidates"]
)


@sourced_candidates_router.get("/", status_code=status.HTTP_200_OK)
async def get_all_sourced_candidates(db=Depends(get_db)):
    """Fetch sourced candidates from MongoDB."""
    return await get_all_sourced_candidate_service()


@sourced_candidates_router.get("/{candidate_id}", status_code=status.HTTP_200_OK)
async def get_sourced_candidate(candidate_id: str, db=Depends(get_db)):
    """Fetch a specific sourced candidate by ID."""
    return await get_sourced_candidate_service(candidate_id)

@sourced_candidates_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sourced_candidate(sourced_candidate: dict, db=Depends(get_db)):
    """Create a new sourced candidate."""
    return await create_sourced_candidate_service(sourced_candidate, db)