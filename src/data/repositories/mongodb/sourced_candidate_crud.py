import logging
import uuid

from src.data.clients.mongodb_client import get_database
from src.data.repositories.mongodb.scoring_crud import get_candidate_score

logger = logging.getLogger(__name__)


async def get_sourced_candidates(job_id: uuid.UUID) -> list:
    try:
        db = await get_database()
        collection = db["sourced_candidates"]
        job_id_str = str(job_id)
        logger.debug(
            f"Querying sourced_candidates collection for job_id: {job_id_str} (type: {type(job_id_str)})"
        )
        candidates = await collection.find({}).to_list(length=None)
        return candidates
    except Exception as e:
        logger.error(
            f"Error fetching sourced candidates for job {job_id}: {e}", exc_info=True
        )
        return []


async def get_candidate_data(candidate_id: str) -> dict | None:
    try:
        db = await get_database()
        collection = db["sourced_candidates"]
        logger.debug(
            f"Querying sourced_candidates for candidate_id: {candidate_id} (type: {type(candidate_id).__name__})"
        )
        candidate = await collection.find_one({"candidate_id": candidate_id})
        if candidate:
            logger.debug(f"Found candidate data with keys: {list(candidate.keys())}")
        else:
            logger.warning(f"No candidate found in DB for candidate_id: {candidate_id}")
            # Try alternative query patterns
            logger.debug("Attempting alternative query with _id lookup...")
            candidate = await collection.find_one({"_id": candidate_id})
            if candidate:
                logger.debug(
                    f"Found candidate using _id lookup: {list(candidate.keys())}"
                )
        return candidate
    except Exception as e:
        logger.error(
            f"Error retrieving candidate data for candidate_id {candidate_id}: {e}",
            exc_info=True,
        )
        return None


async def get_candidate_details(db, candidate_id: str, job_id: str) -> dict | None:
    try:
        score = await get_candidate_score(candidate_id, job_id)
        details = await get_candidate_data(db, candidate_id)
        if not score:
            return None

        candidates_coll = db["sourced_candidates"]
        candidate = await candidates_coll.find_one(
            {"candidate_id": candidate_id, "job_id": job_id}
        )

        return {
            **candidate,
            **score,
            "resume_text": candidate.get("resume_text") if candidate else None,
            "parsed_resume_data": candidate.get("parsed_resume_data")
            if candidate
            else None,
        }
    except Exception:
        return None
