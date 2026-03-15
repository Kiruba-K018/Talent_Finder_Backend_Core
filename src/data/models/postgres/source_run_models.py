import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.data.clients.postgres_client import Base


# SQLAlchemy Model for database persistence
class SourceRuns(Base):
    __tablename__ = "source_runs"

    source_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    schedule: Mapped[str | None] = mapped_column(String(50), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    number_of_resume_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=datetime.utcnow)
    config_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# Pydantic Model for API
class SourcePlatform(BaseModel):
    platform_id: uuid.UUID
    name: str
    base_url: str
    supported_filters: list[str] = Field(default_factory=list)
    last_fetch_at: datetime | None = None
    status: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
