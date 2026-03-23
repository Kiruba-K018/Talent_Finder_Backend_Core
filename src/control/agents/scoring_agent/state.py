from typing import Any, TypedDict
from uuid import UUID


class CandidateStateDict(TypedDict):
    candidate_id: UUID
    resume_text: str
    parsed_data: dict[str, Any]


class ScoringState(TypedDict):
    job_id: UUID
    job_title: str
    job_description: str
    job_skills: list[str]
    candidates: list[CandidateStateDict]
    all_candidates: list[CandidateStateDict]  # All candidates for overflow scoring
    current_candidate_idx: int
    current_candidate_score: dict[str, Any]
    scores_to_save: list[dict[str, Any]]
    shortlist_candidates: list[dict[str, Any]]
    number_of_candidates: int | None
    min_experience: int | None
    max_experience: int | None
    min_educational_qualifications: list | None
    location_preference: str | None
    db: Any | None
    version: int
    total_candidates: int
    processed_candidates: int
    filtered_candidates: int
    scored_candidates: int
    current_stage: str
