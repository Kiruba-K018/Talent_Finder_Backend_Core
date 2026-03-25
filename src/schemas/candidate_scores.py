from uuid import UUID

from pydantic import BaseModel, Field


class CandidateScoreFlag(BaseModel):
    flag_id: int
    flag: str | None = None


class CandidateScoreMissingField(BaseModel):
    missing_field_id: int
    field_name: str | None = None


class CandidateScore(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    job_id: UUID
    rule_based_score: float | None = None
    completion_score: float | None = None
    skill_match_score: float | None = None
    recency_score: float | None = None
    ai_score: float | None = None
    ai_explanation: str | None = None
    confidence_score: float | None = None
    aggregation_score: float | None = None
    flags: list[CandidateScoreFlag] = Field(default_factory=list)
    missing_fields: list[CandidateScoreMissingField] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class CandidateScoreSaveResponse(BaseModel):
    message: str
    count: int = 0


class CandidateScoreRetrieveResponse(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    job_id: UUID
    rule_based_score: float | None = None
    completion_score: float | None = None
    skill_match_score: float | None = None
    ai_score: float | None = None
    ai_explanation: str | None = None
    aggregation_score: float | None = None

    model_config = {"populate_by_name": True}


class CandidateScoreDeleteResponse(BaseModel):
    message: str
    deleted_count: int = 0
