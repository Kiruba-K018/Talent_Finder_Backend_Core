import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.clients.postgres_client import get_db

_scoring_progress = {}

scoring_router = APIRouter(prefix="/api/v1/source-runs", tags=["Source Runs"])


def update_scoring_progress(job_id: str, update: dict):
    """Update progress for a scoring job."""
    if job_id not in _scoring_progress:
        _scoring_progress[job_id] = {
            "job_id": job_id,
            "status": "running",
            "total_candidates": 0,
            "processed_candidates": 0,
            "scored_candidates": 0,
            "filtered_candidates": 0,
            "current_stage": "loading",
            "progress_percent": 0,
            "message": "",
        }

    _scoring_progress[job_id].update(update)

    # Calculate progress percentage
    total = _scoring_progress[job_id].get("total_candidates", 1)
    processed = _scoring_progress[job_id].get("processed_candidates", 0)
    _scoring_progress[job_id]["progress_percent"] = (
        int((processed / total) * 100) if total > 0 else 0
    )


@scoring_router.get("/{job_id}/progress", status_code=status.HTTP_200_OK)
async def get_scoring_progress(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get real-time progress of scoring and shortlisting."""
    try:
        job_uuid = uuid.UUID(job_id)

        if job_id not in _scoring_progress:
            return {
                "job_id": job_id,
                "status": "not_started",
                "total_candidates": 0,
                "processed_candidates": 0,
                "scored_candidates": 0,
                "filtered_candidates": 0,
                "current_stage": "idle",
                "progress_percent": 0,
                "message": "No scoring in progress",
            }

        return _scoring_progress[job_id]

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@scoring_router.get("/{job_id}", status_code=status.HTTP_200_OK)
async def get_source_run_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get source run status (alias for progress endpoint)."""
    return await get_scoring_progress(job_id, db)
