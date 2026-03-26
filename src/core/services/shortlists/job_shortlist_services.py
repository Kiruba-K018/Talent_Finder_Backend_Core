import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.mongodb.scoring_crud import get_candidate_score
from src.data.repositories.mongodb.sourced_candidate_crud import get_candidate_data
from src.data.repositories.postgres.candidate_shortlist_crud import (
    get_job_shortlist_all,
    get_job_shortlist_with_limit,
    get_shortlist_candidate,
    update_candidate_notes,
)
from src.data.repositories.postgres.job_post_crud import get_job_post_by_id
from src.schemas.shortlist_schema import NoteRequest

logger = logging.getLogger(__name__)


async def get_shortlist_for_job_service(
    job_id: str, pg_db: AsyncSession, version: int | None = None
):
    try:
        job_id_uuid = uuid.UUID(job_id)

        # Fetch job post to get required candidates count
        job_post = await get_job_post_by_id(pg_db, job_id_uuid, version=version)
        if not job_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job post {job_id} not found",
            )

        required_count = job_post.no_of_candidates_required

        logger.debug(
            f"Fetching first {required_count} candidates from shortlist "
            f"for job {job_id}"
        )

        # Fetch limited shortlist based on required count
        shortlist_data = await get_job_shortlist_with_limit(
            pg_db, job_id_uuid, required_count, version=version
        )

        if not shortlist_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No shortlist found for job {job_id}",
            )

        return {
            "job_id": shortlist_data.get("job_id"),
            "shortlist": shortlist_data.get("shortlist", []),
            "total_candidates": shortlist_data.get("total_candidates"),
            "required_candidates": required_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching shortlist for job {job_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


async def get_shortlist_all_candidates_service(
    job_id: str, pg_db: AsyncSession, version: int | None = None
):
    """Fetch all candidates from shortlist for a given job and version."""
    try:
        job_id_uuid = uuid.UUID(job_id)

        logger.debug(
            f"Fetching all candidates from shortlist for job {job_id}, "
            f"version {version}"
        )

        # Fetch all shortlist candidates
        shortlist_data = await get_job_shortlist_all(
            pg_db, job_id_uuid, version=version
        )

        if not shortlist_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No shortlist found for job {job_id}",
            )

        return {
            "job_id": shortlist_data.get("job_id"),
            "shortlist": shortlist_data.get("shortlist", []),
            "total_candidates": shortlist_data.get("total_candidates"),
            "version": version if version is not None else 1,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching all shortlist candidates for job {job_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


async def get_shortlists_candidate_details_service(
    job_id: str, candidate_id: str, pg_db: AsyncSession, mongo_db
):
    try:
        # First verify candidate is in the PostgreSQL shortlist for this job
        job_id_uuid = uuid.UUID(job_id)
        logger.info(
            f"Fetching candidate {candidate_id} from shortlist for job {job_id}"
        )

        await get_shortlist_candidate(pg_db, job_id_uuid, candidate_id)
        logger.info(f"Candidate {candidate_id} verified in PostgreSQL shortlist")

        # Now fetch candidate details from MongoDB
        candidate_data = await get_candidate_data(candidate_id)
        candidate_scores = await get_candidate_score(candidate_id, job_id)

        if not candidate_data:
            logger.error(
                f"DATA INTEGRITY ISSUE: Candidate {candidate_id} is in "
                f"PostgreSQL shortlist for job {job_id} but missing from "
                f"MongoDB sourced_candidates collection"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate details not found for {candidate_id}",
            )

        # Merge candidate data with scores (if scores exist)
        scores_data = candidate_scores if candidate_scores else {}
        logger.debug(
            f"Successfully retrieved candidate {candidate_id} with keys: "
            f"{list(candidate_data.keys())}"
        )
        return {**candidate_data, **scores_data}

    except HTTPException:
        # Re-raise HTTPExceptions as-is (don't convert to 500)
        raise
    except ValueError as e:
        logger.error(f"Invalid job_id format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_id format: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving candidate {candidate_id} for "
            f"job {job_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


async def update_shortlisted_candidate_notes_service(
    job_id: str, candidate_id: str, request: NoteRequest, pg_db: AsyncSession
):
    return await update_candidate_notes(
        pg_db, uuid.UUID(job_id), candidate_id, request.note
    )
