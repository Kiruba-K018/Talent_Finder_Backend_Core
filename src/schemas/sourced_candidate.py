from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateExperience(BaseModel):
    experience_id: UUID
    company_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    technology: list[str] = Field(default_factory=list)
    job_role: str | None = None
    job_type: str | None = None


class CandidateProject(BaseModel):
    project_id: UUID
    title: str | None = None
    description: str | None = None
    technology_used: list[str] = Field(default_factory=list)
    duration: str | None = None


class CandidateEducation(BaseModel):
    education_id: UUID
    degree: str | None = None
    course: str | None = None


class CandidateCertification(BaseModel):
    certification_id: UUID
    certification_name: str | None = None
    related_technology: list[str] = Field(default_factory=list)


class SourcedCandidate(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    hash: str | None = None
    candidate_name: str | None = None
    resume_id: UUID
    platform_id: UUID
    sourced_at: datetime | None = None
    source_run_id: UUID | None = None
    updated_on: datetime | None = None
    title: str | None = None
    summary: str | None = None
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    languages_known: list[str] = Field(default_factory=list)
    volunteer_works: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    location: str | None = None
    contact_phone: str | None = None
    candidate_email: str | None = None
    contact_linkedin_url: str | None = None
    portfolio_url: str | None = None
    experience: list[CandidateExperience] = Field(default_factory=list)
    projects: list[CandidateProject] = Field(default_factory=list)
    education: list[CandidateEducation] = Field(default_factory=list)
    certifications: list[CandidateCertification] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class SourcedCandidateResponse(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    candidate_name: str | None = None
    title: str | None = None
    location: str | None = None
    candidate_email: str | None = None
    contact_linkedin_url: str | None = None
    hard_skills: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class SourcedCandidateListResponse(BaseModel):
    candidates: list[SourcedCandidateResponse]
    total: int = 0


class SourcedCandidateDetailResponse(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    hash: str | None = None
    candidate_name: str | None = None
    resume_id: UUID
    platform_id: UUID
    sourced_at: datetime | None = None
    source_run_id: UUID | None = None
    updated_on: datetime | None = None
    title: str | None = None
    summary: str | None = None
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    location: str | None = None
    candidate_email: str | None = None
    contact_linkedin_url: str | None = None

    model_config = {"populate_by_name": True}


class CreateSourcedCandidateResponse(BaseModel):
    message: str
    candidate_id: str | None = None


class SourcedCandidateFetchAllResponse(BaseModel):
    candidates: list[SourcedCandidateResponse]
    total: int = 0


class SourcedCandidateFetchOneResponse(BaseModel):
    id: str = Field(alias="_id")
    candidate_id: UUID
    candidate_name: str | None = None
    title: str | None = None
    location: str | None = None
    candidate_email: str | None = None
    contact_linkedin_url: str | None = None
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class SourcedCandidateDeleteResponse(BaseModel):
    message: str
    deleted_count: int = 0


class SourcedCandidateFetchBySourceRunResponse(BaseModel):
    candidates: list[SourcedCandidateResponse]
    total: int = 0
    source_run_id: str | None = None
