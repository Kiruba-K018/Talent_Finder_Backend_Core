import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.data.repositories.postgres.source_run_crud import upsert_source_run_record, get_all_source_runs, get_one_source_run

logger = logging.getLogger(__name__)


async def create_source_run_record_service(config: dict, db: AsyncSession) -> None:
    """Create or update a source run record in the database.
    
    Expected fields in config:
    - source_run_id: str (UUID)
    - platform_id: str (UUID)
    - status: str ("completed" or "failed")
    - number_of_resume_fetched: int
    - config_id: str (UUID) - corresponds to sourcing_config.id
    - run_at: str (ISO format datetime)
    - completed_at: str (ISO format datetime)
    """
    try:
        # Parse and validate the incoming data
        source_run_id = uuid.UUID(config.get("source_run_id"))
        platform_id = uuid.UUID(config.get("platform_id"))
        config_id = uuid.UUID(config.get("config_id"))
        
        # Parse datetime strings if they're provided as strings
        run_at = config.get("run_at")
        if isinstance(run_at, str):
            run_at = datetime.fromisoformat(run_at)
        
        completed_at = config.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        
        source_run_data = {
            "source_run_id": source_run_id,
            "platform_id": platform_id,
            "status": config.get("status", "completed"),
            "number_of_resume_fetched": int(config.get("number_of_resume_fetched", 0)),
            "config_id": config_id,
            "run_at": run_at or datetime.utcnow(),
            "completed_at": completed_at,
        }
        
        await upsert_source_run_record(db, source_run_data)
        logger.info(
            "source_run_created_or_updated: "
            f"source_run_id={str(source_run_id)}, status={source_run_data['status']}, "
            f"profiles_fetched={source_run_data['number_of_resume_fetched']}"
        )
    except Exception as e:
        logger.error(f"Error creating/updating source run record: {str(e)}", exc_info=True)
        raise




async def fetch_all_source_runs_service(db: AsyncSession) -> list:
    try:
        result = await get_all_source_runs(db)
        return result
    except Exception as e:
        logger.error(f"Error fetching source runs: {str(e)}", exc_info=True)
        raise e

async def fetch_one_source_run_service(db: AsyncSession, source_run_id: uuid.UUID):
    try:
        result = await get_one_source_run(db, source_run_id)
        return result
    except Exception as e:
        logger.error(f"Error fetching source run {source_run_id}: {str(e)}", exc_info=True)
        raise e