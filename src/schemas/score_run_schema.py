from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ScoreRunCreate(BaseModel):
    job_id: UUID
    job_version: int
    triggered_by: UUID | None = None


class ScoreEventCreate(BaseModel):
    score_run_id: UUID
    job_id: UUID
    job_version: int
    event: str
    data: dict


class ScoreRunResponse(BaseModel):
    score_run_id: UUID
    job_id: UUID
    job_version: int
    status: str
    error_message: str | None
    triggered_by: UUID | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScoreEventResponse(BaseModel):
    event_id: int
    score_run_id: UUID
    job_id: UUID
    job_version: int
    event: str
    data: dict
    emitted_at: datetime

    model_config = {"from_attributes": True}
