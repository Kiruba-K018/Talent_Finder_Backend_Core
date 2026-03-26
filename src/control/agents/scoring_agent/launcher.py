import logging
import uuid

from src.control.agents.scoring_agent.graph import graph
from src.control.agents.scoring_agent.prepare_states import prepare_state

logger = logging.getLogger(__name__)


def push_progress_update(job_id: uuid.UUID, progress_data: dict):
    """Push progress update to tracking system."""
    try:
        from src.api.rest.routes.source_runs.source_runs import update_scoring_progress

        update_scoring_progress(str(job_id), progress_data)
    except ImportError:
        logger.warning("Could not import progress update function")


async def launch_scoring_agent(job_id: uuid.UUID, job_data: dict):
    initial_state = await prepare_state(job_id=job_id, job_data=job_data)
    if initial_state is None:
        logger.error(f"Failed to prepare initial state for job {job_id}")
        push_progress_update(
            job_id,
            {
                "status": "failed",
                "current_stage": "failed",
                "message": "Failed to prepare initial state",
            },
        )
        return None

    logger.info(
        f"""Invoking scoring graph for job {job_id} with 
        {len(initial_state.get("candidates", []))} candidates"""
    )
    push_progress_update(
        job_id,
        {
            "status": "running",
            "current_stage": "loading",
            "total_candidates": len(initial_state.get("candidates", [])),
            "message": "Starting candidate evaluation...",
        },
    )

    result = await graph.ainvoke(initial_state)

    logger.info(
        f"""[END] Scoring agent completed for job {job_id}. Created shortlist with 
        {len(result.get("shortlist_candidates", []))} candidates"""
    )
    push_progress_update(
        job_id,
        {
            "status": "completed",
            "current_stage": "completed",
            "processed_candidates": result.get("total_candidates", 0),
            "scored_candidates": len(result.get("shortlist_candidates", [])),
            "filtered_candidates": result.get("filtered_candidates", 0),
            "message": (
                f"Shortlist created with "
                f"{len(result.get('shortlist_candidates', []))} candidates"
            ),
        },
    )

    return result
