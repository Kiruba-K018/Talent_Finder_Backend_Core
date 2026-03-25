from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SourceRunResponse(BaseModel):
    source_run_id: UUID
    config: dict | None = None

    class Config:
        from_attributes = True


class SourceRunListResponse(BaseModel):
    source_runs: list[SourceRunResponse]


class SourceRunDetailResponse(BaseModel):
    source_run_id: UUID
    job_id: UUID | None = None
    config: dict | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class SourceRunDeleteResponse(BaseModel):
    message: str


class SourceRunInsertResponse(BaseModel):
    message: str
    source_run_id: UUID | None = None


class SourceRunUpsertResponse(BaseModel):
    message: str
    source_run_id: UUID | None = None


class SourceRunFetchAllResponse(BaseModel):
    source_runs: list[dict]
    total: int = 0


class SourceRunFetchOneResponse(BaseModel):
    source_run_id: str
    platform_id: str | None = None
    status: str | None = None
    schedule: str | None = None
    skills: str | None = None
    location: str | None = None
    number_of_resume_fetched: int = 0
    run_at: str | None = None
    config_id: str | None = None
    error_message: str | None = None
    completed_at: str | None = None
