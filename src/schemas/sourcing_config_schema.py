from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SourcingConfigCreate(BaseModel):
    frequency: str = Field(..., description="Frequency of sourcing runs (e.g., 'daily', 'weekly')")
    scheduled_time: str | time = Field(..., description="Time of day to run the sourcing (e.g., '02:00:00')")
    scheduled_day: str | None = Field(None, description="Day of the week for weekly runs (e.g., 'Monday')")
    search_skills: list[str] = Field(..., description="List of skills to search for")
    search_location: str = Field(..., description="Location to search for candidates")
    max_profiles: int = Field(..., description="Maximum number of profiles to source")

    @field_validator('scheduled_time', mode='before')
    @classmethod
    def validate_scheduled_time(cls, v):
        if isinstance(v, time):
            return v.isoformat()  # Convert time object to ISO string
        if isinstance(v, str):
            try:
                time.fromisoformat(v)  # Validate the string format
                return v  # Return the valid string
            except ValueError as e:
                raise ValueError(f"Invalid time format: {v}. Expected HH:MM:SS") from e
        raise ValueError(f"scheduled_time must be str or time object, got {type(v).__name__}")


class SourcingConfigResponse(BaseModel):
    id: UUID
    org_id: UUID
    is_active: bool
    frequency: str
    scheduled_time: time
    scheduled_day: str | None
    search_skills: list[str]
    search_location: str
    max_profiles: int
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    created_by: UUID


class SourcingConfigDeleteResponse(BaseModel):
    message: str


class SourcingConfigCreateResponse(BaseModel):
    id: UUID
    org_id: UUID
    is_active: bool
    frequency: str
    scheduled_time: time
    scheduled_day: str | None
    search_skills: list[str]
    search_location: str
    max_profiles: int
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    created_by: UUID


class SourcingConfigUpdateResponse(BaseModel):
    id: UUID
    org_id: UUID
    is_active: bool
    frequency: str
    scheduled_time: time
    scheduled_day: str | None
    search_skills: list[str]
    search_location: str
    max_profiles: int
    next_run_at: datetime | None
    created_at: datetime
    created_by: UUID

