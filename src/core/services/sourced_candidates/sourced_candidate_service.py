import logging

from fastapi import HTTPException, status

from src.data.repositories.mongodb.sourced_candidate_crud import (
    delete_sourced_candidate,
    get_candidate_data,
    get_sourced_candidates,
    get_sourced_candidates_by_source_run,
    insert_sourced_candidate,
)

logger = logging.getLogger(__name__)


async def get_all_sourced_candidate_service():
    try:
        candidates = await get_sourced_candidates(
            job_id="3fa85f64-5717-4562-b3fc-2c963f66afa6"
        )
        return {"candidates": candidates, "count": len(candidates)}
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sourced candidates: {str(err)}",
        ) from err


async def get_sourced_candidate_service(candidate_id: str):
    try:
        candidate = await get_candidate_data(candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sourced candidate with ID {candidate_id} not found",
            )
        return candidate
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sourced candidate: {str(err)}",
        ) from err


async def create_sourced_candidate_service(sourced_candidate: dict, db):
    try:
        # Ensure candidate has an identifier
        if "_id" in sourced_candidate and "candidate_id" not in sourced_candidate:
            sourced_candidate["candidate_id"] = str(sourced_candidate["_id"])

        await insert_sourced_candidate(db, sourced_candidate)
        return {"message": "Sourced candidate created successfully"}

    except Exception as err:
        logger.error(f"Error creating sourced candidate: {str(err)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sourced candidate: {str(err)}",
        ) from err


async def delete_sourced_candidate_service(candidate_id: str):
    res = await delete_sourced_candidate(candidate_id)
    if res:
        return {"message": "Sourced candidate deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sourced candidate with ID {candidate_id} not found",
        )


async def get_sourced_candidate_by_source_run_service(source_run_id: str):
    try:
        candidates = await get_sourced_candidates_by_source_run(
            source_run_id=source_run_id
        )
        return {"candidates": candidates, "count": len(candidates)}
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sourced candidates for source run "
            f"{source_run_id}: {str(err)}",
        ) from err
