import asyncio
import logging
import sys
import uuid

from langgraph.graph import END
from src.data.repositories.postgres.candidate_shortlist_crud import create_job_shortlist

from src.control.agents.scoring_agent.state import ScoringState
from src.control.agents.scoring_agent.utils import (
    aggregate_scores,
    calculate_ai_score,
    calculate_field_completion_score,
    calculate_recency_score,
    calculate_rule_based_score,
    calculate_skill_match_score,
    detect_flags,
)
from src.data.clients.postgres_client import get_session_factory
from src.data.repositories.mongodb.scoring_crud import save_candidate_scores
from src.data.repositories.mongodb.sourced_candidate_crud import get_candidate_data

logger = logging.getLogger(__name__)

# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)  # Changed from DEBUG to INFO for performance
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # Changed from DEBUG to INFO


async def load_candidates_node(state: ScoringState) -> ScoringState:
    logger.info(f"Loading candidates for job {state['job_id']}")
    total = len(state["candidates"])
    logger.info(f"[PROGRESS] Stage: loading | Total: {total} candidates")
    return {
        **state,
        "current_candidate_idx": 0,
        "scores_to_save": [],
        "shortlist_candidates": [],
        "filtered_candidates": 0,
        "below_threshold_candidates": [],
        "processing_fallback": False,
        "total_candidates": total,
        "processed_candidates": 0,
        "scored_candidates": 0,
        "current_stage": "loading",
    }


async def score_single_candidate(
    candidate, state: ScoringState
) -> tuple[dict | None, str | None, int]:
    """Score a single candidate. Returns (score_doc, candidate_id, status)."""
    try:
        completion_score = await calculate_field_completion_score(
            candidate["parsed_data"]
        )

        rule_score, rule_details = await calculate_rule_based_score(
            candidate["parsed_data"],
            state["job_title"],
            state.get("min_educational_qualifications", ""),
            state.get("location_preference", ""),
            state.get("min_experience", 0),
        )

        recency_score = await calculate_recency_score(candidate["parsed_data"])

        skill_score, skill_details = await calculate_skill_match_score(
            candidate["candidate_id"], state["job_skills"]
        )

        candidate_id_str = str(candidate["candidate_id"])
        candidate_data = await get_candidate_data(candidate_id_str)

        if not candidate_data:
            logger.warning(f"Candidate {candidate_id_str}: no data found")
            return None, candidate_id_str, 2  # 2 = no data

        aggregate_score = await aggregate_scores(
            completion_score, rule_score, recency_score, skill_score
        )

        flags = await detect_flags(
            candidate["parsed_data"],
            {
                "min_experience": state.get("min_experience", 0),
                "max_experience": state.get("max_experience", 100),
                "min_educational_qualifications": state.get(
                    "min_educational_qualifications", ""
                ),
                "location_preference": state.get("location_preference", ""),
            },
        )

        score_doc = {
            "_id": str(uuid.uuid4()),
            "candidate_id": str(candidate["candidate_id"]),
            "job_id": str(state["job_id"]),
            "rule_based_score": round(rule_score, 2),
            "completion_score": round(completion_score, 2),
            "skill_match_score": round(skill_score, 2),
            "recency_score": round(recency_score, 2),
            "ai_score": 0,
            "ai_explanation": "",
            "confidence_score": 0,
            "aggregation_score": round(aggregate_score, 2),
            "flags": [{"flag": f["flag"], "reason": f.get("reason")} for f in flags],
            "missing_fields": [],
        }

        logger.info(
            f"Candidate {candidate['candidate_id']} scored: aggregate={round(aggregate_score, 2)}"
        )
        return score_doc, str(candidate["candidate_id"]), 0  # 0 = success

    except Exception as e:
        logger.error(f"Error scoring candidate {candidate.get('candidate_id')}: {e}")
        return None, str(candidate.get("candidate_id")), 3  # 3 = error


async def process_candidate_node(state: ScoringState) -> ScoringState:
    """Process multiple candidates concurrently in batches."""
    batch_size = 4  # Process 4 candidates at a time
    candidates = state["candidates"]
    start_idx = state["current_candidate_idx"]
    total = len(candidates)

    if start_idx >= total:
        logger.info(f"All candidates processed for job {state['job_id']}")
        return state

    end_idx = min(start_idx + batch_size, total)
    batch = candidates[start_idx:end_idx]

    logger.info(
        f"Processing batch of {len(batch)} candidates ({start_idx + 1}-{end_idx}/{total})"
    )
    logger.info(
        f"[PROGRESS] Stage: processing | Batch: {start_idx + 1}-{end_idx}/{total} | Progress: {int((end_idx / total) * 100)}%"
    )

    # Score all candidates in batch concurrently
    results = await asyncio.gather(
        *[score_single_candidate(c, state) for c in batch], return_exceptions=True
    )

    scores_to_add = []
    shortlist_to_add = []
    filtered_count = state.get("filtered_candidates", 0)
    scored_count = state.get("scored_candidates", 0)

    for score_doc, candidate_id, status in results:
        if isinstance(status, Exception):
            logger.error(f"Exception in batch processing: {status}")
            continue

        if status == 0:  # Success - scored
            scores_to_add.append(score_doc)
            shortlist_to_add.append(
                {
                    "candidate_id": candidate_id,
                    "aggregation_score": score_doc["aggregation_score"],
                    "score_doc_id": score_doc["_id"],
                }
            )
            scored_count += 1
        elif status == 1:  # Filtered
            filtered_count += 1

    processed = end_idx
    logger.info(
        f"[PROGRESS-DETAIL] Processed: {processed}/{total} | Scored: {scored_count} | Filtered: {filtered_count}"
    )

    return {
        **state,
        "current_candidate_idx": end_idx,
        "scores_to_save": state["scores_to_save"] + scores_to_add,
        "shortlist_candidates": state["shortlist_candidates"] + shortlist_to_add,
        "filtered_candidates": filtered_count,
        "processed_candidates": processed,
        "scored_candidates": scored_count,
        "current_stage": "processing",
    }


async def continue_processing(state: ScoringState) -> str:
    if state["current_candidate_idx"] < len(state["candidates"]):
        return "process_candidate"
    return END


async def save_scores_node(state: ScoringState) -> ScoringState:
    total_candidates = state.get("total_candidates", len(state["candidates"]))
    scored_candidates = len(state["scores_to_save"])
    filtered_candidates = state.get("filtered_candidates", 0)

    logger.info(
        f"[PROGRESS] Stage: scoring | Completed: {scored_candidates}/{total_candidates} candidates scored | {filtered_candidates} filtered"
    )

    if scored_candidates == 0:
        logger.warning(
            f"No candidates passed the scoring threshold for job {state['job_id']}"
        )
        return {**state, "current_stage": "scoring"}

    logger.info(f"Saving {scored_candidates} scores for job {state['job_id']}")
    try:
        await save_candidate_scores(state["scores_to_save"])
        logger.info(f"Successfully saved scores for job {state['job_id']}")
    except Exception as e:
        logger.error(f"Failed to save scores for job {state['job_id']}: {e}")

    return {**state, "current_stage": "scoring"}


async def calculate_ai_scores_for_shortlist(state: ScoringState) -> ScoringState:
    try:
        shortlist = state["shortlist_candidates"]
        scores_to_save = state["scores_to_save"]

        for candidate in shortlist:
            candidate_data = await get_candidate_data(str(candidate["candidate_id"]))
            (
                ai_score,
                confidence_score,
                ai_explanation,
                flags,
            ) = await calculate_ai_score(
                candidate_data,
                state["job_title"],
                state["job_description"],
                state["min_experience"],
                state["min_educational_qualifications"],
            )
            candidate["ai_score"] = round(ai_score, 2)
            candidate["ai_explanation"] = ai_explanation
            candidate["confidence_score"] = round(confidence_score * 0.9, 2)
            candidate["flags"] = flags
            candidate["aggregation_score"] = (
                candidate["aggregation_score"] + candidate["ai_score"] * 0.20
            )  # Re-aggregate with AI score

            # Update the corresponding score document in scores_to_save
            for score_doc in scores_to_save:
                if score_doc["_id"] == candidate["score_doc_id"]:
                    score_doc["ai_score"] = candidate["ai_score"]
                    score_doc["ai_explanation"] = candidate["ai_explanation"]
                    score_doc["confidence_score"] = candidate["confidence_score"]
                    score_doc["aggregation_score"] = candidate["aggregation_score"]
                    break

            logger.info(
                f"Candidate {candidate['candidate_id']} AI score: {round(ai_score, 2)} | Confidence: {round(confidence_score * 0.9, 2)} | New aggregate: {round(candidate['aggregation_score'], 2)}"
            )

        return {
            **state,
            "shortlist_candidates": shortlist,
            "scores_to_save": scores_to_save,
        }
    except Exception as e:
        logger.error(f"Error calculating AI scores for shortlist: {e}")
        return state  # Return state without AI scores if there's an error


async def create_shortlist_node(state: ScoringState) -> ScoringState:
    logger.info(
        f"Creating shortlist for job {state['job_id']} with {len(state['shortlist_candidates'])} candidates"
    )
    logger.info("[PROGRESS] Stage: shortlisting | Creating shortlist...")

    state["shortlist_candidates"] = sorted(
        state["shortlist_candidates"],
        key=lambda x: x["aggregation_score"],
        reverse=True,
    )

    sorted_shortlist = state["shortlist_candidates"][
        : state["number_of_candidates"] or len(state["shortlist_candidates"])
    ]

    logger.info(
        f"Top {state['number_of_candidates']} candidates for shortlist: {[c['candidate_id'] for c in sorted_shortlist]}"
    )
    logger.info(
        f"[PROGRESS] Stage: shortlisting | Selected {len(sorted_shortlist)} candidates for shortlist"
    )
    return {
        **state,
        "shortlist_candidates": sorted_shortlist,
        "current_stage": "shortlisting",
    }


async def save_shortlist_to_db(state: ScoringState) -> ScoringState:
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            logger.debug(f"Saving shortlist to database for job {state['job_id']}")
            await create_job_shortlist(
                db=db,
                job_id=state["job_id"],
                sorted_shortlist=state["shortlist_candidates"],
            )
        logger.info(f"Successfully created shortlist for job {state['job_id']}")
        logger.info(
            f"[PROGRESS] Stage: completed | Shortlist created successfully with {len(state['shortlist_candidates'])} candidates"
        )
    except Exception as e:
        logger.error(f"Failed to create shortlist for job {state['job_id']}: {e}")

    return {**state, "current_stage": "completed"}
