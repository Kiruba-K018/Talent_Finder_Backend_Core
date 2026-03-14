import logging
import sys
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.jobs_shortlist_models import JobCandidateShortlist

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


async def create_job_shortlist(
    db: AsyncSession, job_id: uuid.UUID, sorted_shortlist: list[dict], version: int = 1) -> bool:
    logger.info(
        f"[START] Creating shortlist for job {job_id} with {len(sorted_shortlist)} candidates"
    )
    logger.debug(f"Shortlist data structure: {sorted_shortlist}")
    try:
        for idx, candidate in enumerate(sorted_shortlist):
            logger.debug(
                f"Processing candidate {idx + 1}/{len(sorted_shortlist)}: {candidate.get('candidate_id')}"
            )
            logger.debug(f"Candidate fields: {candidate.keys()}")

            try:
                job_shortlist = JobCandidateShortlist(
                    job_candidate_id=uuid.uuid4(),
                    job_id=job_id,
                    version=version,
                    candidate_id=candidate["candidate_id"],
                    recruiter_notes=candidate.get("recruiter_notes"),
                    reviewed_by=candidate.get("reviewed_by"),
                )
                db.add(job_shortlist)
                logger.debug(f"Added candidate {candidate['candidate_id']} to session")
            except Exception as e:
                logger.error(
                    f"Error adding candidate {candidate.get('candidate_id')} to session: {e}",
                    exc_info=True,
                )
                raise

        logger.info(
            f"Committing {len(sorted_shortlist)} candidates to database for job {job_id}"
        )
        await db.commit()
        logger.info(f"[SUCCESS] Successfully created shortlist for job {job_id}")
        return True
    except Exception as e:
        logger.error(
            f"[ERROR] Failed to create shortlist for job {job_id}: {e}", exc_info=True
        )
        try:
            await db.rollback()
            logger.info(f"Transaction rolled back for job {job_id}")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        return False


async def get_job_shortlist(db: AsyncSession, job_id: uuid.UUID, version: int | None = None) -> dict | None:
    try:
        version = version if version is not None else 1
        logger.debug(f"Fetching shortlist for job {job_id}")
        result = await db.execute(
            select(JobCandidateShortlist).where(JobCandidateShortlist.job_id == job_id, 
                                                JobCandidateShortlist.version == version)
                                                )
        shortlist = result.scalars().all()
        logger.info(f"Found {len(shortlist)} candidates in shortlist for job {job_id}")
        return {
            "job_id": job_id,
            "shortlist": [
                {
                    "candidate_id": item.candidate_id,
                    "recruiter_notes": item.recruiter_notes,
                    "reviewed_by": item.reviewed_by,
                }
                for item in shortlist
            ],
        }
    except Exception as e:
        logger.error(f"Failed to fetch shortlist for job {job_id}: {e}", exc_info=True)
        return None


async def update_candidate_notes(
    db: AsyncSession, job_id: uuid.UUID, candidate_id: str, notes: str,
    version: int | None = None) -> bool:
    try:
        version = version if version is not None else 1
        logger.debug(f"Updating notes for candidate {candidate_id} in job {job_id}")
        result = await db.execute(
            update(JobCandidateShortlist)
            .where(
                (JobCandidateShortlist.job_id == job_id)
                & (JobCandidateShortlist.candidate_id == candidate_id)
                & (JobCandidateShortlist.version == version)
            )
            .values(
                recruiter_notes=notes,
                reviewed_by="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            )
        )
        await db.commit()
        logger.info(
            f"Successfully updated notes for candidate {candidate_id} in job {job_id}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to update notes for candidate {candidate_id} in job {job_id}: {e}",
            exc_info=True,
        )
        try:
            await db.rollback()
            logger.info(
                f"Transaction rolled back while updating notes for candidate {candidate_id} in job {job_id}"
            )
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        return False


async def delete_job_shortlist(db: AsyncSession, job_id: uuid.UUID) -> None:
    try:
        logger.debug(f"Deleting shortlist for job {job_id}")
        result = await db.execute(
            select(JobCandidateShortlist).where(JobCandidateShortlist.job_id == job_id)
        )
        shortlists = result.scalars().all()
        for shortlist in shortlists:
            await db.delete(shortlist)
        await db.commit()
        logger.info(f"Deleted {len(shortlists)} shortlist entries for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to delete shortlist for job {job_id}: {e}", exc_info=True)
        try:
            await db.rollback()
            logger.info(
                f"Transaction rolled back while deleting shortlist for job {job_id}"
            )
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")


async def get_shortlist_candidate(
    db: AsyncSession, job_id: uuid.UUID, candidate_id: str,  version: int | None = None
) -> JobCandidateShortlist:
    
    version = version if version is not None else 1
    result = await db.execute(
        select(JobCandidateShortlist).where(
            (JobCandidateShortlist.job_id == job_id)
            & (JobCandidateShortlist.candidate_id == candidate_id)
            & (JobCandidateShortlist.version == version)
        )
    )
    shortlist_entry = result.scalars().first()

    if not shortlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"""Candidate {candidate_id} not found 
            in shortlist for job {job_id}""",
        )
