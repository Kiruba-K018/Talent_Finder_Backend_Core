from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import requires_recruiter
from src.core.services.shortlists.job_shortlist_services import (
    get_shortlist_for_job_service,
    get_shortlists_candidate_details_service,
    update_shortlisted_candidate_notes_service,
)
from src.data.clients.mongodb_client import get_db as get_mongo_db
from src.data.clients.postgres_client import get_db
from src.schemas.shortlist_schema import NoteRequest

candidate_shortlist_router = APIRouter(
    prefix="/api/v1/shortlist", tags=["Candidate Shortlist"]
)


@candidate_shortlist_router.get("/{job_id}", status_code=status.HTTP_200_OK)
async def get_shortlisted_candidates(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    return await get_shortlist_for_job_service(job_id, db)

@candidate_shortlist_router.get("/{job_id}/version/{version}", status_code=status.HTTP_200_OK)
async def get_shortlisted_candidates_version(
    job_id: str,
    version: int,
    db: AsyncSession = Depends(get_db)
):
    return await get_shortlist_for_job_service(job_id, db, version=version)

@candidate_shortlist_router.get(
    "/{job_id}/{candidate_id}", status_code=status.HTTP_200_OK
)
async def get_shortlisted_candidate_details(
    job_id: str,
    candidate_id: str,
    pg_db: AsyncSession = Depends(get_db),
    mongo_db=Depends(get_mongo_db)
):
    return await get_shortlists_candidate_details_service(
        job_id, candidate_id, pg_db, mongo_db
    )


@candidate_shortlist_router.put(
    "/{job_id}/{candidate_id}", status_code=status.HTTP_200_OK
)
async def update_shortlisted_candidate_notes(
    job_id: str,
    candidate_id: str,
    request: NoteRequest,
    pg_db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_recruiter),
):
    return await update_shortlisted_candidate_notes_service(
        job_id, candidate_id, request, pg_db
    )
