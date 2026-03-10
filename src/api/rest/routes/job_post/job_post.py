import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import requires_admin, requires_recruiter
from src.core.services.job_post.job_post_services import (
    close_job_post_service,
    create_new_job_post_service,
    delete_all_job_posts_service,
    list_all_jobs_service,
    retrieve_job_post_service,
    update_job_post_service,
)
from src.data.clients.postgres_client import get_db
from src.schemas.job_post_schema import (
    JobPostCloseResponse,
    JobPostCreate,
    JobPostListResponse,
    JobPostResponse,
    JobPostUpdate,
)

job_post_router = APIRouter(prefix="/api/v1/jobpost", tags=["Job Post"])


@job_post_router.get(
    "/", response_model=JobPostListResponse, status_code=status.HTTP_200_OK
)
async def list_job_posts(db: AsyncSession = Depends(get_db)) -> JobPostListResponse:
    return await list_all_jobs_service(db)


@job_post_router.get(
    "/{job_id}", response_model=JobPostResponse, status_code=status.HTTP_200_OK
)
async def retrieve_job_post(
    job_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> JobPostResponse:
    return await retrieve_job_post_service(db, job_id)


@job_post_router.post(
    "/", response_model=JobPostResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_job_post(
    payload: JobPostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_recruiter),
) -> JobPostResponse:
    # only recruiters (and above) can create jobs
    return await create_new_job_post_service(
        db, payload, background_tasks, current_user
    )


@job_post_router.put(
    "/{job_id}", response_model=JobPostResponse, status_code=status.HTTP_200_OK
)
async def update_existing_job_post(
    job_id: uuid.UUID,
    payload: JobPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_recruiter),
) -> JobPostResponse:
    return await update_job_post_service(db, job_id, payload)


@job_post_router.put(
    "/{job_id}/close",
    response_model=JobPostCloseResponse,
    status_code=status.HTTP_200_OK,
)
async def close_existing_job_post(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(requires_recruiter),
) -> JobPostCloseResponse:
    return await close_job_post_service(db, job_id)


@job_post_router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_job_posts(
    db: AsyncSession = Depends(get_db), current_user=Depends(requires_admin)
):
    return await delete_all_job_posts_service(db)
