import logging
import uuid

from motor.motor_asyncio import AsyncIOMotorClient
from src.config.settings import setting
from src.data.clients.mongodb_client import get_database
from src.data.repositories.mongodb.scoring_crud import get_candidate_score
from src.schemas.sourced_candidate import (
    SourcedCandidateFetchAllResponse,
    SourcedCandidateFetchOneResponse,
    SourcedCandidateFetchBySourceRunResponse,
)

logger = logging.getLogger(__name__)


async def get_sourced_candidates_with_fresh_client(job_id: uuid.UUID) -> list:
    """
    Fetch sourced candidates using a fresh MongoDB connection.
    This is critical for background tasks which run in separate event loops.
    Using the global motor client from a different event loop causes:
    "Task got Future attached to a different loop" errors.
    """
    fresh_client = None
    try:
        logger.info(f"Creating fresh MongoDB connection for job {job_id}")
        fresh_client = AsyncIOMotorClient(
            setting.mongo_uri,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            uuidRepresentation="standard",
        )
        db = fresh_client[setting.mongo_db]
        collection = db["sourced_candidates"]
        logger.info(f"Querying sourced_candidates collection for job {job_id}")
        candidates = await collection.find({}).to_list(length=None)
        logger.info(f"Successfully fetched {len(candidates)} candidates for job {job_id}")
        return candidates
    except Exception as e:
        logger.error(
            f"Error fetching sourced candidates for job {job_id}: {e}", exc_info=True
        )
        return []
    finally:
        if fresh_client:
            fresh_client.close()
            logger.debug(f"Closed fresh MongoDB connection for job {job_id}")


async def get_candidate_data_with_fresh_client(candidate_id: str) -> dict | None:
    """
    Fetch candidate data using a fresh MongoDB connection.
    This is critical for background tasks which run in separate event loops.
    Using the global motor client from a different event loop causes:
    "Task got Future attached to a different loop" errors.
    """
    fresh_client = None
    try:
        logger.debug(f"Creating fresh MongoDB connection for candidate {candidate_id}")
        fresh_client = AsyncIOMotorClient(
            setting.mongo_uri,
            maxPoolSize=10,
            minPoolSize=2,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            uuidRepresentation="standard",
        )
        db = fresh_client[setting.mongo_db]
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
    finally:
        if fresh_client:
            fresh_client.close()
            logger.debug(f"Closed fresh MongoDB connection for candidate {candidate_id}")


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


async def insert_sourced_candidate(db, candidate_data: dict) -> dict | None:
    try:
        # Ensure collection exists by listing collections first
        collection_list = await db.list_collection_names()
        if "sourced_candidates" not in collection_list:
            logger.info("Creating sourced_candidates collection...")
            await db.create_collection("sourced_candidates")
        
        # Map _id from sourcing service to candidate_id for this collection
        if "_id" in candidate_data and "candidate_id" not in candidate_data:
            candidate_data["candidate_id"] = str(candidate_data["_id"])
        
        # Ensure candidate_id is set to avoid null unique key violations
        if not candidate_data.get("candidate_id"):
            candidate_data["candidate_id"] = str(candidate_data.get("_id", "unknown"))
        
        collection = db["sourced_candidates"]
        
        # Try to insert, handle duplicate key errors gracefully
        try:
            result = await collection.insert_one(candidate_data)
            if result.inserted_id:
                logger.debug(f"Inserted sourced candidate with ID: {result.inserted_id}")
                return candidate_data
            else:
                logger.error("Failed to insert sourced candidate, no ID returned")
                return None
        except Exception as insert_error:
            # Check if it's a duplicate key error
            if "duplicate key" in str(insert_error).lower():
                logger.debug(f"Candidate already exists, attempting update instead: {candidate_data.get('candidate_id')}")
                # Update existing instead of insert
                result = await collection.update_one(
                    {"candidate_id": candidate_data.get("candidate_id")},
                    {"$set": candidate_data},
                    upsert=True
                )
                logger.debug(f"Updated/upserted candidate: {candidate_data.get('candidate_id')}")
                return candidate_data
            else:
                raise
    except Exception as e:
        logger.error(f"Error inserting sourced candidate: {e}", exc_info=True)
        return None

async def delete_sourced_candidate(candidate_id: str) -> bool:
    try:
        db = await get_database()
        collection = db["sourced_candidates"]
        result = await collection.delete_one({"candidate_id": candidate_id})
        if result.deleted_count == 1:
            logger.debug(f"Deleted sourced candidate with ID: {candidate_id}")
            return True
        else:
            logger.warning(f"No sourced candidate found to delete with ID: {candidate_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting sourced candidate with ID {candidate_id}: {e}", exc_info=True)
        return False


async def get_sourced_candidates_by_source_run(source_run_id: str) -> list:
    try:
        db = await get_database()
        collection = db["sourced_candidates"]
        logger.debug(
            f"Querying sourced_candidates for source_run_id: {source_run_id} (type: {type(source_run_id).__name__})"
        )
        candidates = await collection.find({"source_run_id": source_run_id}).to_list(length=None)
        logger.debug(f"Found {len(candidates)} candidates for source_run_id: {source_run_id}")
        return candidates
    except Exception as e:
        logger.error(f"Error fetching sourced candidates for source run {source_run_id}: {e}", exc_info=True)
        return []