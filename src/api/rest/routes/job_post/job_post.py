import uuid

from fastapi import APIRouter, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import _admin_user, _db, _recruiter_user
from src.core.services.job_post.job_post_services import (
    close_job_post_service,
    create_new_job_post_service,
    delete_all_job_posts_service,
    list_all_jobs_service,
    retrieve_job_post_service,
    retrieve_versioned_job_post_service,
    update_job_post_service,
)
from src.schemas.job_post_schema import (
    JobPostCloseResponse,
    JobPostCreate,
    JobPostDeleteResponse,
    JobPostListResponse,
    JobPostResponse,
    JobPostUpdate,
)

job_post_router = APIRouter(prefix="/api/v1/jobpost", tags=["Job Post"])


@job_post_router.get(
    "/", response_model=JobPostListResponse, status_code=status.HTTP_200_OK
)
async def list_job_posts(db: AsyncSession = _db) -> JobPostListResponse:
    """Retrieve all job posts.

    Returns complete list of all published job posts with pagination support.

    Args:
        db: Database session for job post queries.

    Returns:
        JobPostListResponse: List of job posts with metadata.
    """
    return await list_all_jobs_service(db)


@job_post_router.get(
    "/{job_id}", response_model=JobPostResponse, status_code=status.HTTP_200_OK
)
async def retrieve_job_post(
    job_id: uuid.UUID, db: AsyncSession = _db
) -> JobPostResponse:
    """Retrieve a specific job post by ID.

    Returns complete details of the latest version of the job post.

    Args:
        job_id: UUID of the job post.
        db: Database session for job post lookup.

    Returns:
        JobPostResponse: Job post details.

    Raises:
        HTTPException: 404 if job post not found.
    """
    return await retrieve_job_post_service(db, job_id)


@job_post_router.get(
    "/{job_id}/version/{version}",
    response_model=JobPostResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_job_post_version(
    job_id: uuid.UUID, version: int, db: AsyncSession = _db
) -> JobPostResponse:
    """Retrieve a specific version of a job post.

    Returns details of a specific historical version of the job post.

    Args:
        job_id: UUID of the job post.
        version: Version number to retrieve.
        db: Database session for job post lookup.

    Returns:
        JobPostResponse: Job post details for the specified version.

    Raises:
        HTTPException: 404 if job post or version not found.
    """
    return await retrieve_versioned_job_post_service(db, job_id, version=version)


@job_post_router.post(
    "/", response_model=JobPostResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_job_post(
    payload: JobPostCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = _db,
    current_user=_recruiter_user,
) -> JobPostResponse:
    """Create a new job post.

    Only recruiter users can create job posts. Triggers background job sourcing tasks.

    Args:
        payload: JobPostCreate with job details (title, description, requirements).
        background_tasks: FastAPI background tasks for async sourcing.
        db: Database session for job post creation.
        current_user: Authenticated recruiter user.

    Returns:
        JobPostResponse: Created job post with id and version.

    Raises:
        HTTPException: 400 for invalid input, 403 if not recruiter.
    """
    return await create_new_job_post_service(
        db, payload, background_tasks, current_user
    )


@job_post_router.put(
    "/{job_id}", response_model=JobPostResponse, status_code=status.HTTP_200_OK
)
async def update_existing_job_post(
    job_id: uuid.UUID,
    payload: JobPostUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = _db,
    current_user=_recruiter_user,
) -> JobPostResponse:
    """Update an existing job post.

    Only recruiter users can update job posts. Creates new version history entry.

    Args:
        job_id: UUID of the job post to update.
        payload: JobPostUpdate with updated job details.
        background_tasks: FastAPI background tasks for async sourcing.
        db: Database session for update operation.
        current_user: Authenticated recruiter user.

    Returns:
        JobPostResponse: Updated job post with new version.

    Raises:
        HTTPException: 404 if job post not found, 403 if not recruiter.
    """
    return await update_job_post_service(
        db, job_id, payload, current_user, background_tasks
    )


@job_post_router.put(
    "/{job_id}/close",
    response_model=JobPostCloseResponse,
    status_code=status.HTTP_200_OK,
)
async def close_existing_job_post(
    job_id: uuid.UUID,
    db: AsyncSession = _db,
    current_user=_recruiter_user,
) -> JobPostCloseResponse:
    """Close an active job post.

    Only recruiter users can close job posts. Prevents new sourcing but retains records.

    Args:
        job_id: UUID of the job post to close.
        db: Database session for update operation.
        current_user: Authenticated recruiter user.

    Returns:
        JobPostCloseResponse: Confirmation of job post closure.

    Raises:
        HTTPException: 404 if job post not found, 403 if not recruiter.
    """
    return await close_job_post_service(db, job_id, current_user)


@job_post_router.delete("/", status_code=200, response_model=JobPostDeleteResponse)
async def delete_all_job_posts(
    db: AsyncSession = _db,
    current_user=_admin_user,
) -> JobPostDeleteResponse:
    """Delete all job posts from the system.

    Only admin users can perform this operation. This is a destructive action.

    Args:
        db: Database session for deletion operation.
        current_user: Authenticated admin user.

    Returns:
        JobPostDeleteResponse: Confirmation message of deletion.

    Raises:
        HTTPException: 403 if not admin.
    """
    await delete_all_job_posts_service(db)
    return JobPostDeleteResponse(message="All job posts deleted successfully")
