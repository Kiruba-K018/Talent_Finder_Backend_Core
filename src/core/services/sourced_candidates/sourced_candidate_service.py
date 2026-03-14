from fastapi import HTTPException, status
from src.data.clients.mongodb_client import get_db
from src.data.repositories.mongodb.sourced_candidate_crud import (
    get_candidate_data,
    get_sourced_candidates,
    insert_sourced_candidate
)

async def get_all_sourced_candidate_service():
    try:
        candidates = await get_sourced_candidates(
            job_id="3fa85f64-5717-4562-b3fc-2c963f66afa6"
        )
        return {"candidates": candidates, "count": len(candidates)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sourced candidates: {str(e)}",
        )
    


async def get_sourced_candidate_service( candidate_id: str):
    try:
        candidate = await get_candidate_data(db, candidate_id)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sourced candidate with ID {candidate_id} not found",
            )
        return candidate
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sourced candidate: {str(e)}",
        )


async def create_sourced_candidate_service(sourced_candidate: dict, db):
    try:
        await insert_sourced_candidate(sourced_candidate, db)
        return {"message": "Sourced candidate created successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sourced candidate: {str(e)}",
        )