import logging
import uuid

from motor.motor_asyncio import AsyncIOMotorClient

from src.config.settings import setting
from src.data.clients.mongodb_client import get_database

logger = logging.getLogger(__name__)


async def save_candidate_scores(scores: list[dict]) -> bool:
    try:
        db = await get_database()
        collection = db["candidate_scores"]
        if scores:
            logger.info(f"Saving {len(scores)} candidate scores to MongoDB")
            result = await collection.insert_many(scores)
            logger.info(f"Successfully saved {len(result.inserted_ids)} scores")
        return True
    except Exception as e:
        logger.error(f"Failed to save candidate scores: {e}", exc_info=True)
        return False


async def save_candidate_scores_with_fresh_client(scores: list[dict]) -> bool:
    """
    Save candidate scores using a fresh MongoDB connection.
    This is critical for background tasks which run in separate event loops.
    """
    fresh_client = None
    try:
        fresh_client = AsyncIOMotorClient(
            setting.mongo_uri,
            maxPoolSize=10, minPoolSize=2,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True, retryReads=True,
            uuidRepresentation="standard",
        )
        db = fresh_client[setting.mongo_db]
        collection = db["candidate_scores"]
        if scores:
            logger.info(f"Saving {len(scores)} candidate scores to MongoDB with fresh client")
            result = await collection.insert_many(scores)
            logger.info(f"Successfully saved {len(result.inserted_ids)} scores with fresh client")
        return True
    except Exception as e:
        logger.error(f"Failed to save candidate scores with fresh client: {e}", exc_info=True)
        return False
    finally:
        if fresh_client:
            fresh_client.close()


async def get_candidate_score(candidate_id: str, job_id: str) -> dict | None:
    try:
        db = await get_database()
        collection = db["candidate_scores"]
        score = await collection.find_one(
            {"candidate_id": candidate_id, "job_id": job_id}
        )
        return score
    except Exception as e:
        logger.error(
            f"Error retrieving candidate score for candidate {candidate_id} and job {job_id}: {e}"
        )
        return None


async def delete_job_scores(db, job_id: uuid.UUID) -> None:
    try:
        db = await get_database()
        collection = db["candidate_scores"]
        result = await collection.delete_many({"job_id": str(job_id)})
        logger.info(f"Deleted {result.deleted_count} scores for job {job_id}")
    except Exception as e:
        logger.error(f"Error deleting scores for job {job_id}: {e}", exc_info=True)
