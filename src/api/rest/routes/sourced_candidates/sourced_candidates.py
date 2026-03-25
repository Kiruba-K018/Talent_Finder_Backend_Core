from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter

from src.data.clients.mongodb_client import get_db
from src.core.services.sourced_candidates.sourced_candidate_service import (
    get_sourced_candidate_service,
    get_all_sourced_candidate_service,
    create_sourced_candidate_service,
    delete_sourced_candidate_service,
    get_sourced_candidate_by_source_run_service
)
from src.schemas.sourced_candidate import (
    SourcedCandidateResponse,
    SourcedCandidateListResponse,
    SourcedCandidateDetailResponse,
    CreateSourcedCandidateResponse,
)   


sourced_candidates_router = APIRouter(
    prefix="/api/v1/sourced-candidates", tags=["Sourced Candidates"]
)


@sourced_candidates_router.get("/", status_code=status.HTTP_200_OK, response_model=SourcedCandidateListResponse)
async def get_all_sourced_candidates(db=Depends(get_db))-> SourcedCandidateListResponse:
    """Retrieve all sourced candidates.
    
    Returns complete list of all candidates sourced from external sources.
    
    Args:
        db: MongoDB database session.
    
    Returns:
        SourcedCandidateListResponse: List of all sourced candidates with metadata.
    """
    return await get_all_sourced_candidate_service()


@sourced_candidates_router.get("/{candidate_id}", status_code=status.HTTP_200_OK, response_model=SourcedCandidateDetailResponse)
async def get_sourced_candidate(candidate_id: str, db=Depends(get_db))-> SourcedCandidateDetailResponse:
    """Retrieve a specific sourced candidate by ID.
    
    Returns complete details of a sourced candidate including resume and metadata.
    
    Args:
        candidate_id: String ID of the sourced candidate.
        db: MongoDB database session.
    
    Returns:
        SourcedCandidateDetailResponse: Detailed candidate information.
    
    Raises:
        HTTPException: 404 if candidate not found.
    """
    return await get_sourced_candidate_service(candidate_id)

@sourced_candidates_router.get("/by-source-run/{source_run_id}", status_code=status.HTTP_200_OK, response_model=SourcedCandidateListResponse)
async def get_sourced_candidates_by_source_run(source_run_id: str, db=Depends(get_db))-> SourcedCandidateListResponse:
    """Retrieve sourced candidates for a specific source run.
    
    Returns all candidates sourced during a specific sourcing execution.
    
    Args:
        source_run_id: String ID of the source run.
        db: MongoDB database session.
    
    Returns:
        SourcedCandidateListResponse: List of candidates from the source run.
    
    Raises:
        HTTPException: 400 if source run ID is invalid.
    """
    try:
        return await get_sourced_candidate_by_source_run_service(source_run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sourced_candidates_router.post("/", status_code=status.HTTP_201_CREATED, response_model=CreateSourcedCandidateResponse)
async def create_sourced_candidate(sourced_candidate: dict, db=Depends(get_db))-> CreateSourcedCandidateResponse:
    """Create a new sourced candidate record.
    
    Adds a new candidate to the sourced candidates collection.
    
    Args:
        sourced_candidate: Dictionary containing candidate data.
        db: MongoDB database session.
    
    Returns:
        CreateSourcedCandidateResponse: Created candidate with id.
    
    Raises:
        HTTPException: 400 for invalid candidate data.
    """
    return await create_sourced_candidate_service(sourced_candidate, db)

@sourced_candidates_router.delete("/{candidate_id}/", status_code=status.HTTP_200_OK, response_model=CreateSourcedCandidateResponse)
async def delete_sourced_candidate(candidate_id: str, db=Depends(get_db))-> CreateSourcedCandidateResponse:
    """Delete a sourced candidate record.
    
    Removes a candidate from the sourced candidates collection.
    
    Args:
        candidate_id: String ID of the candidate to delete.
        db: MongoDB database session.
    
    Returns:
        CreateSourcedCandidateResponse: Confirmation message of deletion.
    
    Raises:
        HTTPException: 404 if candidate not found.
    """
    await delete_sourced_candidate_service(candidate_id)
    return CreateSourcedCandidateResponse(message=f"Candidate {candidate_id} deleted successfully")
    