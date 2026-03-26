import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.source_run_models import SourceRuns

logger = logging.getLogger(__name__)


async def insert_source_run_record(db: AsyncSession, source_run_data: dict) -> bool:
    """Insert a new source run record into the database."""
    try:
        # Ensure UUIDs are proper UUID objects, not strings
        data_to_insert = {
            "source_run_id": uuid.UUID(source_run_data["source_run_id"])
            if isinstance(source_run_data.get("source_run_id"), str)
            else source_run_data.get("source_run_id"),
            "platform_id": uuid.UUID(source_run_data["platform_id"])
            if isinstance(source_run_data.get("platform_id"), str)
            else source_run_data.get("platform_id"),
            "config_id": uuid.UUID(source_run_data["config_id"])
            if isinstance(source_run_data.get("config_id"), str)
            else source_run_data.get("config_id"),
            "status": source_run_data.get("status", "completed"),
            "number_of_resume_fetched": int(
                source_run_data.get("number_of_resume_fetched", 0)
            ),
            "run_at": source_run_data.get("run_at") or datetime.utcnow(),
            "completed_at": source_run_data.get("completed_at"),
        }
        new_source_run = SourceRuns(**data_to_insert)
        db.add(new_source_run)
        await db.commit()
        logger.info(f"Source run inserted: {data_to_insert.get('source_run_id')}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error inserting source run: {str(e)}", exc_info=True)
        raise e


async def upsert_source_run_record(db: AsyncSession, source_run_data: dict) -> bool:
    """Create or update a source run record in the database."""
    try:
        source_run_id = (
            uuid.UUID(source_run_data.get("source_run_id"))
            if isinstance(source_run_data.get("source_run_id"), str)
            else source_run_data.get("source_run_id")
        )

        # Check if record exists
        result = await db.execute(
            select(SourceRuns).where(SourceRuns.source_run_id == source_run_id)
        )
        existing_run = result.scalar_one_or_none()

        if existing_run:
            # Update existing record - only update specific fields
            existing_run.status = source_run_data.get("status", existing_run.status)
            existing_run.number_of_resume_fetched = int(
                source_run_data.get(
                    "number_of_resume_fetched", existing_run.number_of_resume_fetched
                )
            )
            existing_run.completed_at = (
                source_run_data.get("completed_at") or datetime.utcnow()
            )
            logger.info(f"Source run updated: {source_run_id}")
        else:
            # Create new record
            data_to_insert = {
                "source_run_id": source_run_id,
                "platform_id": uuid.UUID(source_run_data["platform_id"])
                if isinstance(source_run_data.get("platform_id"), str)
                else source_run_data.get("platform_id"),
                "config_id": uuid.UUID(source_run_data["config_id"])
                if isinstance(source_run_data.get("config_id"), str)
                else source_run_data.get("config_id"),
                "status": source_run_data.get("status", "completed"),
                "number_of_resume_fetched": int(
                    source_run_data.get("number_of_resume_fetched", 0)
                ),
                "run_at": source_run_data.get("run_at") or datetime.utcnow(),
                "completed_at": source_run_data.get("completed_at"),
            }
            new_source_run = SourceRuns(**data_to_insert)
            db.add(new_source_run)
            logger.info(f"Source run created: {source_run_id}")

        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error upserting source run: {str(e)}", exc_info=True)
        raise e


async def get_all_source_runs(db: AsyncSession) -> list:
    """Fetch all source run records from the database."""
    try:
        result = await db.execute(select(SourceRuns))
        source_runs = result.scalars().all()
        return [
            {
                "source_run_id": str(run.source_run_id),
                "platform_id": str(run.platform_id) if run.platform_id else None,
                "status": run.status,
                "schedule": run.schedule,
                "skills": run.skills,
                "location": run.location,
                "number_of_resume_fetched": run.number_of_resume_fetched,
                "run_at": run.run_at.isoformat() if run.run_at else None,
                "config_id": str(run.config_id) if run.config_id else None,
                "error_message": run.error_message,
                "completed_at": run.completed_at.isoformat()
                if run.completed_at
                else None,
            }
            for run in source_runs
        ]
    except Exception as e:
        logger.error(f"Error fetching source runs: {str(e)}")
        raise e


async def get_one_source_run(db: AsyncSession, source_run_id: uuid.UUID) -> dict | None:
    """Fetch a single source run record by its ID."""
    try:
        result = await db.execute(
            select(SourceRuns).where(SourceRuns.source_run_id == source_run_id)
        )
        source_run = result.scalar_one_or_none()
        if source_run:
            return {
                "source_run_id": str(source_run.source_run_id),
                "platform_id": str(source_run.platform_id)
                if source_run.platform_id
                else None,
                "status": source_run.status,
                "schedule": source_run.schedule,
                "skills": source_run.skills,
                "location": source_run.location,
                "number_of_resume_fetched": source_run.number_of_resume_fetched,
                "run_at": source_run.run_at.isoformat() if source_run.run_at else None,
                "config_id": str(source_run.config_id)
                if source_run.config_id
                else None,
                "error_message": source_run.error_message,
                "completed_at": source_run.completed_at.isoformat()
                if source_run.completed_at
                else None,
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching source run {source_run_id}: {str(e)}")
        raise e


async def delete_source_run(db: AsyncSession, source_run_id: uuid.UUID) -> bool:
    """Delete a source run record by its ID."""
    try:
        result = await db.execute(
            select(SourceRuns).where(SourceRuns.source_run_id == source_run_id)
        )
        source_run = result.scalar_one_or_none()
        if source_run:
            await db.delete(source_run)
            await db.commit()
            logger.info(f"Source run {source_run_id} deleted")
            return True
        logger.warning(f"Source run {source_run_id} not found for deletion")
        return False
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Error deleting source run {source_run_id}: {str(e)}", exc_info=True
        )
        raise e
