import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.data.clients.postgres_client import Base


class JobPostModel(Base):
    __tablename__ = "job_posts"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_educational_qualifications: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    job_type: Mapped[str | None] = mapped_column(String, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    location_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Open")
    no_of_candidates_required: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )


class JdEnrichmentModel(Base):
    __tablename__ = "jd_enrichments"

    enrichment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    enrichment_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_educational_qualifications: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    location_preference: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
