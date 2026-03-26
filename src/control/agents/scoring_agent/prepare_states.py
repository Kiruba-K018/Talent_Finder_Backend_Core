import logging
import sys
import uuid

from src.control.agents.scoring_agent.state import CandidateStateDict, ScoringState
from src.data.repositories.mongodb.sourced_candidate_crud import (
    get_sourced_candidates_with_fresh_client,
)

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


initial_state: ScoringState


async def prepare_state(job_id: uuid.UUID, job_data: dict):
    try:
        logger.info(f"[START] Launching scoring agent for job {job_id}")
        logger.debug(f"Job data keys: {job_data.keys() if job_data else 'None'}")

        job_skills = [
            {"required": skill} for skill in job_data.get("required_skills", [])
        ] + [{"preferred": skill} for skill in job_data.get("preferred_skills", [])]

        initial_state: ScoringState = {
            "job_id": job_id,
            "job_title": job_data.get("job_title", ""),
            "job_description": job_data.get("job_description", ""),
            "job_skills": job_skills,
            "candidates": [],
            "all_candidates": [],  # Store all candidates for overflow scoring
            "current_candidate_idx": 0,
            "current_candidate_score": {},
            "scores_to_save": [],
            "shortlist_candidates": [],
            "min_experience": job_data.get("min_experience", 0),
            "max_experience": job_data.get("max_experience", 0),
            "min_educational_qualifications": job_data.get(
                "min_educational_qualifications", []
            ),
            "location_preference": job_data.get("location_preference", ""),
            "number_of_candidates": job_data.get("number_of_candidates_required", 0),
            "version": job_data.get("version", 1),
            "db": None,
        }

        # Use fresh MongoDB connection via repository to avoid
        # "Future attached to different loop" error. Critical for background
        # tasks running in separate event loops
        logger.info("Fetching sourced candidates with fresh MongoDB connection")
        candidates_list = await get_sourced_candidates_with_fresh_client(job_id)
        logger.info(f"Found {len(candidates_list)} sourced candidates for job {job_id}")

        if not candidates_list:
            logger.warning(
                f"No sourced candidates found for job {job_id}. Returning empty state."
            )
            logger.info(
                f"[END] Successfully prepared initial state for job {job_id} "
                f"(no candidates)"
            )
            return initial_state

        candidates: list[CandidateStateDict] = []
        for cand in candidates_list:
            try:
                candidate_id = cand.get("candidate_id", "")
                if not candidate_id:
                    logger.warning("Candidate missing candidate_id, skipping")
                    continue

                candidates.append(
                    {
                        "candidate_id": uuid.UUID(candidate_id),
                        "resume_text": cand.get("resume_text", ""),
                        "parsed_data": cand.get("parsed_resume_data", {}),
                    }
                )

                from src.core.services.job_post.embeddings import embed_resume_skills

                hard_skills = cand.get("parsed_resume_data", {}).get("hard_skills", [])
                if hard_skills:
                    await embed_resume_skills(candidate_id, hard_skills)

            except Exception as e:
                logger.error(
                    f"Error processing candidate {cand.get('candidate_id')}: {e}"
                )
                continue

        logger.info(f"Processed {len(candidates)} candidates for scoring")
        initial_state["candidates"] = candidates
        initial_state["all_candidates"] = candidates  # Store for overflow scoring later
        logger.info(f"[END] Successfully prepared initial state for job {job_id}")
        return initial_state
    except Exception as e:
        logger.error(f"Got error {e} in preparing initial state", exc_info=True)
        return None
