import uuid
from datetime import UTC, datetime, time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.models.postgres.sourcing_config_models import SourcingConfig as SourcingConfigModel
from datetime import timedelta

async def create_or_update_sourcing_config(
        db:AsyncSession,
        config_data: dict,
) :
    # Check if a config already exists for the organization
    result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.org_id == config_data.get("org_id"), SourcingConfigModel.is_active == True))
    existing_config = result.scalars().first()
    scheduled_time = config_data.get("scheduled_time")
    
    # Check if it's already a datetime/time object
    if isinstance(scheduled_time, (datetime, time)):
        local_time = scheduled_time.time() if isinstance(scheduled_time, datetime) else scheduled_time
    elif isinstance(scheduled_time, str):
        local_time = time.fromisoformat(scheduled_time)
    else:
        raise ValueError(f"scheduled_time must be str or datetime, got {type(scheduled_time)}")
    
    if scheduled_time:
        try:
            # Parse scheduled_time and convert to UTC (assuming scheduled_time is in local time)
            config_data["scheduled_time"] = local_time
        except ValueError:
            raise ValueError("Invalid time format for scheduled_time. Expected HH:MM:SS.")
        
    if existing_config:
        # Update the existing config
        existing_config.frequency = config_data.get("frequency")
        existing_config.scheduled_time = config_data.get("scheduled_time")
        existing_config.scheduled_day = config_data.get("scheduled_day")
        existing_config.search_skills = config_data.get("search_skills")
        existing_config.search_location = config_data.get("search_location")
        existing_config.max_profiles = config_data.get("max_profiles")
        existing_config.is_active = True  # Reactivate if it was deactivated
        db.add(existing_config)
    else:
        # Create a new config
        new_config = SourcingConfigModel(
            org_id=config_data.get("org_id"),
            frequency=config_data.get("frequency"),
            scheduled_time=config_data.get("scheduled_time"),
            scheduled_day=config_data.get("scheduled_day"),
            search_skills=config_data.get("search_skills"),
            search_location=config_data.get("search_location"),
            max_profiles=config_data.get("max_profiles"),
            is_active=True,
            created_by=config_data.get("created_by"),
            created_at = datetime.now(UTC)
        )
        db.add(new_config)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise e 
    return existing_config if existing_config else new_config


async def get_sourcing_config_by_org(db: AsyncSession, org_id: uuid.UUID):
    result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.org_id == org_id, SourcingConfigModel.is_active == True))
    return result.scalars().first()

async def deactivate_sourcing_config(db: AsyncSession, org_id: uuid.UUID):
    result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.org_id == org_id, SourcingConfigModel.is_active == True))
    config = result.scalars().first()
    if config:
        config.is_active = False
        db.add(config)
        await db.commit()
        return True
    return False

async def get_all_sourcing_configs(db: AsyncSession, org_id: uuid.UUID):
    result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.org_id == org_id))
    return result.scalars().all()

async def get_sourcing_config_by_id(db: AsyncSession, config_id: uuid.UUID):
    result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.id == config_id))
    return result.scalars().first()