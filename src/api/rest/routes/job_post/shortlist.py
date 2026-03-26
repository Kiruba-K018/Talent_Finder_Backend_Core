from fastapi import APIRouter, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import _db, _mongodb, _recruiter_user
from src.core.services.shortlists.job_shortlist_services import (
    get_shortlist_all_candidates_service,
    get_shortlist_for_job_service,
    get_shortlists_candidate_details_service,
    update_shortlisted_candidate_notes_service,
)
from src.schemas.shortlist_schema import (
    CandidateDetailsResponse,
    NoteRequest,
    ShortlistResponse,
    UpdateNotesResponse,
)

candidate_shortlist_router = APIRouter(
    prefix="/api/v1/shortlist", tags=["Candidate Shortlist"]
)


@candidate_shortlist_router.get(
    "/{job_id}", status_code=status.HTTP_200_OK, response_model=ShortlistResponse
)
async def get_shortlisted_candidates(
    job_id: str,
    version: int = Query(None),
    db: AsyncSession = _db,
) -> ShortlistResponse:
    """Get shortlisted candidates for a job.

    Returns the top N candidates from the shortlist where N is
    no_of_candidates_required.

    Args:
        job_id: String ID of the job post.
        version: Optional version number for historical shortlist.
        db: Database session for data retrieval.

    Returns:
        ShortlistResponse: List of shortlisted candidates with scores.

    Raises:
        HTTPException: 404 if job post not found.
    """
    return await get_shortlist_for_job_service(job_id, db, version=version)


@candidate_shortlist_router.get(
    "/{job_id}/all/version/{version}",
    status_code=status.HTTP_200_OK,
    response_model=ShortlistResponse,
)
async def get_all_shortlisted_candidates_version(
    job_id: str, version: int, db: AsyncSession = _db
) -> ShortlistResponse:
    """Get all shortlisted candidates for a specific job version.

    Returns complete shortlist for the specified job post version without limit.

    Args:
        job_id: String ID of the job post.
        version: Version number for historical shortlist.
        db: Database session for data retrieval.

    Returns:
        ShortlistResponse: Complete list of shortlisted candidates with scores.

    Raises:
        HTTPException: 404 if job post or version not found.
    """
    return await get_shortlist_all_candidates_service(job_id, db, version=version)


@candidate_shortlist_router.get(
    "/{job_id}/version/{version}",
    status_code=status.HTTP_200_OK,
    response_model=ShortlistResponse,
)
async def get_shortlisted_candidates_version(
    job_id: str, version: int, db: AsyncSession = _db
) -> ShortlistResponse:
    """Get top N shortlisted candidates for a specific job version.

    Returns the top N candidates from shortlist where N is no_of_candidates_required.

    Args:
        job_id: String ID of the job post.
        version: Version number for historical shortlist.
        db: Database session for data retrieval.

    Returns:
        ShortlistResponse: Top N shortlisted candidates with scores.

    Raises:
        HTTPException: 404 if job post or version not found.
    """
    return await get_shortlist_for_job_service(job_id, db, version=version)


@candidate_shortlist_router.get(
    "/{job_id}/{candidate_id}",
    status_code=status.HTTP_200_OK,
    response_model=CandidateDetailsResponse,
)
async def get_shortlisted_candidate_details(
    job_id: str,
    candidate_id: str,
    pg_db: AsyncSession = _db,
    mongo_db=_mongodb,
) -> CandidateDetailsResponse:
    """Retrieve detailed information about a shortlisted candidate.

    Returns comprehensive candidate details including resume, scores, and notes.

    Args:
        job_id: String ID of the job post.
        candidate_id: String ID of the candidate.
        pg_db: PostgreSQL database session.
        mongo_db: MongoDB database session for candidate details.

    Returns:
        CandidateDetailsResponse: Comprehensive candidate information.

    Raises:
        HTTPException: 404 if job post or candidate not found.
    """
    return await get_shortlists_candidate_details_service(
        job_id, candidate_id, pg_db, mongo_db
    )


@candidate_shortlist_router.put(
    "/{job_id}/{candidate_id}",
    status_code=status.HTTP_200_OK,
    response_model=UpdateNotesResponse,
)
async def update_shortlisted_candidate_notes(
    job_id: str,
    candidate_id: str,
    request: NoteRequest,
    pg_db: AsyncSession = _db,
    current_user=_recruiter_user,
) -> UpdateNotesResponse:
    """Update notes for a shortlisted candidate.

    Only recruiter users can update candidate notes. Notes are persisted
    per candidate-job pair.

    Args:
        job_id: String ID of the job post.
        candidate_id: String ID of the candidate.
        request: NoteRequest containing the notes to update.
        pg_db: Database session for update operation.
        current_user: Authenticated recruiter user.

    Returns:
        UpdateNotesResponse: Confirmation of notes update.

    Raises:
        HTTPException: 404 if job post or candidate not found, 403 if not recruiter.
    """
    return await update_shortlisted_candidate_notes_service(
        job_id, candidate_id, request, pg_db
    )
