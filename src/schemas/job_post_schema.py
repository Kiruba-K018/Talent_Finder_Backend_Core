from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class JobPostCreate(BaseModel):
    job_title: str = Field(..., description="Title of the job position")
    job_description: str = Field(..., description="Detailed description of the job")
    min_experience: int = Field(0, description="Minimum years of experience required")
    max_experience: int = Field(0, description="Maximum years of experience required")
    min_education_qualifications: list[str] = Field(default_factory=list)
    location_preference: str | None = Field(None)
    job_type: Literal["Full-time", "Part-time", "Contract", "Internship"] = Field(...)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    no_of_candidates_required: int = Field(1)
    created_by: UUID | None = Field(None)


class JobPostUpdate(BaseModel):
    job_title: str | None = None
    job_description: str | None = None
    min_experience: int | None = None
    max_experience: int | None = None
    min_education_qualifications: list[str] | None = None
    location_preference: str | None = None
    job_type: Literal["Full-time", "Part-time", "Contract", "Internship"] | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    no_of_candidates_required: int | None = None


class JobPostResponse(BaseModel):
    job_id: UUID
    job_title: str
    description: str | None = None
    min_experience: int | None = None
    max_experience: int | None = None
    min_educational_qualifications: str | None = None
    job_type: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    location_preference: str | None = None
    status: str
    no_of_candidates_required: int | None = None
    created_by: UUID | None = None
    version: int

    model_config = {"from_attributes": True}


class JobPostListResponse(BaseModel):
    job_posts: list[JobPostResponse]


class JobPostCloseResponse(BaseModel):
    job_id: UUID
    status: Literal["Closed"]


class JobPostDeleteResponse(BaseModel):
    message: str


class JobPostAllResponse(BaseModel):
    job_posts: list[JobPostResponse]


class JobPostCreateResponse(BaseModel):
    job_id: UUID
    job_title: str
    description: str | None = None
    job_type: str | None = None
    status: str
    version: int
    created_by: UUID | None = None

    model_config = {"from_attributes": True}


class JobPostUpdateResponse(BaseModel):
    job_id: UUID
    job_title: str | None = None
    description: str | None = None
    job_type: str | None = None
    status: str
    version: int
    updated_by: UUID | None = None

    model_config = {"from_attributes": True}
