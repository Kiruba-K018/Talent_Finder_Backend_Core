import uuid
from datetime import UTC, datetime, time, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.models.postgres.sourcing_config_models import SourcingConfig as SourcingConfigModel

# IST = UTC+5:30 (Indian Standard Time)
IST = timezone(timedelta(hours=5, minutes=30))


def _calculate_next_run_at(
    frequency: str,
    scheduled_time: time,
    scheduled_day: str = None,
    now: datetime = None
) -> datetime:
    """Calculate the next run time based on frequency and scheduled time (in IST)."""
    if now is None:
        # Use IST timezone (UTC+5:30)
        now = datetime.now(IST)
    else:
        # If provided datetime is UTC or timezone-naive, convert to IST
        if now.tzinfo is None or now.tzinfo == UTC:
            now = now.astimezone(IST)
    
    if frequency == "hourly":
        # For hourly, next run is 1 hour from now
        return now + timedelta(hours=1)
    
    elif frequency == "daily":
        # For daily, schedule at the specified time today or tomorrow
        if scheduled_time is None:
            scheduled_time = time(0, 0)  # Default to midnight
        
        # Create a datetime for today at the scheduled time
        next_run = now.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=0,
            microsecond=0,
        )
        
        # If the scheduled time has already passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    elif frequency == "weekly":
        # For weekly, schedule for the specified day and time
        if scheduled_time is None:
            scheduled_time = time(0, 0)  # Default to midnight
        if scheduled_day is None:
            scheduled_day = "monday"  # Default to Monday
        
        # Map day names to weekday numbers (Monday=0, Sunday=6)
        day_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        
        target_day = day_map.get(scheduled_day.lower(), 0)
        current_day = now.weekday()
        
        # Calculate days until target day
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0:
            # It's the target day - check if time has passed
            next_run = now.replace(
                hour=scheduled_time.hour,
                minute=scheduled_time.minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                days_ahead = 7  # Schedule for next week
        
        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=0,
            microsecond=0,
        )
        
        return next_run
    
    # Default: run in 1 hour
    return now + timedelta(hours=1)
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
    
    # Calculate next_run_at based on frequency and scheduled time
    frequency = config_data.get("frequency", "daily")
    scheduled_day = config_data.get("scheduled_day")
    next_run_at = _calculate_next_run_at(frequency, local_time, scheduled_day)
    
    if existing_config:
        # Update the existing config
        existing_config.frequency = config_data.get("frequency")
        existing_config.scheduled_time = config_data.get("scheduled_time")
        existing_config.scheduled_day = config_data.get("scheduled_day")
        existing_config.search_skills = config_data.get("search_skills")
        existing_config.search_location = config_data.get("search_location")
        existing_config.max_profiles = config_data.get("max_profiles")
        existing_config.is_active = True  # Reactivate if it was deactivated
        # Update next_run_at when updating the schedule
        existing_config.next_run_at = next_run_at
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
            created_at=datetime.now(UTC),
            next_run_at=next_run_at,  #Set initial next_run_at
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


async def get_sourcing_config_by_id(db: AsyncSession, config_id: uuid.UUID):
    try:
        result = await db.execute(select(SourcingConfigModel).where(SourcingConfigModel.id == config_id))
        return result.scalars().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))