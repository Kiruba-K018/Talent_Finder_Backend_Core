import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from src.data.clients.postgres_client import Base


class JobCandidateShortlist(Base):
    __tablename__ = "job_candidate_shortlist"

    job_candidate_id = Column(UUID, primary_key=True, default=uuid.uuid4())
    job_id = Column(UUID, ForeignKey("job_posts.job_id"), nullable=False)
    candidate_id = Column(UUID, nullable=False)
    recruiter_notes = Column(String, nullable=True)
    reviewed_by = Column(UUID, ForeignKey("users.user_id"), nullable=True)
