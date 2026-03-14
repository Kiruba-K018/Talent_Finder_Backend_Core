import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SourcePlatform(BaseModel):
    platform_id: uuid.UUID
    name: str
    base_url: str
    supported_filters: list[str] = Field(default_factory=list)
    last_fetch_at: datetime | None = None
    status: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None


class SourceRun(BaseModel):
    source_run_id: uuid.UUID
    platform_id: uuid.UUID
    status: str
    number_of_resume_fetched: int = Field(default=0)
    job_id: uuid.UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
