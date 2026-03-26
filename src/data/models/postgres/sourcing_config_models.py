import uuid
from datetime import datetime, time

from sqlalchemy import ARRAY, Boolean, DateTime, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.data.clients.postgres_client import Base


class SourcingConfig(Base):
    __tablename__ = "sourcing_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)
    scheduled_day: Mapped[str | None] = mapped_column(String(20), nullable=True)
    search_skills: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=[]
    )
    search_location: Mapped[str] = mapped_column(String(255), nullable=False)
    max_profiles: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
