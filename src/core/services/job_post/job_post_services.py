import logging
import sys
import uuid

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.control.agents.scoring_agent.launcher import launch_scoring_agent
from src.data.repositories.mongodb.scoring_crud import delete_job_scores
from src.data.repositories.postgres.candidate_shortlist_crud import delete_job_shortlist
from src.data.repositories.postgres.job_post_crud import (
    close_job_post,
    create_job_post,
    delete_job_post,
    get_all_job_posts,
    get_job_post_by_id,
    update_job_post,
)
from src.schemas.job_post_schema import (
    JobPostCloseResponse,
    JobPostCreate,
    JobPostListResponse,
    JobPostResponse,
    JobPostUpdate,
)

logger = logging.getLogger(__name__)
# Ensure logger is configured with console handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("""%(asctime)s - %(name)s - 
    %(levelname)s - %(message)s""")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


async def list_all_jobs_service(db: AsyncSession) -> JobPostListResponse:
    job_posts = await get_all_job_posts(db)
    return JobPostListResponse(
        job_posts=[JobPostResponse.model_validate(j) for j in job_posts]
    )


async def retrieve_job_post_service(
    db: AsyncSession, job_id: uuid.UUID
) -> JobPostResponse:
    job_post = await get_job_post_by_id(db, job_id)
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post {job_id} not found.",
        )
    return JobPostResponse.model_validate(job_post)

async def retrieve_versioned_job_post_service(
        db: AsyncSession, job_id: uuid.UUID, version: int
)-> JobPostResponse:
    job_post = await get_job_post_by_id(db, job_id, version=version)
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post {job_id} with version {version} not found.",
        )
    return JobPostResponse.model_validate(job_post)


async def create_new_job_post_service(
    db: AsyncSession,
    payload: JobPostCreate,
    background_tasks: BackgroundTasks,
    current_user,
) -> JobPostResponse:
    logger.info(f"Creating new job post with title: {payload.job_title}")
    payload.created_by = current_user.user_id
    job_post = await create_job_post(db, payload)
    logger.info(f"Job post created successfully with id: {job_post.job_id}")

    job_data = {
        "job_id": str(job_post.job_id),
        "job_title": job_post.job_title,
        "job_description": job_post.description,
        "required_skills": job_post.required_skills,
        "preferred_skills": job_post.preferred_skills,
        "min_experience": job_post.min_experience,
        "max_experience": job_post.max_experience,
        "min_educational_qualifications": job_post.min_educational_qualifications,
        "location_preference": job_post.location_preference,
        "number_of_candidates_required": job_post.no_of_candidates_required,
        
    }

    logger.info(f"""Adding launch_scoring_agent task to background 
    for job {job_post.job_id}""")
    background_tasks.add_task(launch_scoring_agent, job_post.job_id, job_data)
    logger.info(f"Background task scheduled for job {job_post.job_id}")

    return JobPostResponse.model_validate(job_post)


async def update_job_post_service(
    db: AsyncSession, job_id: uuid.UUID, payload: JobPostUpdate, current_user, background_tasks: BackgroundTasks
) -> JobPostResponse:
    job_post = await get_job_post_by_id(db, job_id)
    
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post {job_id} not found.",
        )
    if job_post.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to update this job post.",
        )
    update_data = await update_job_post(db, job_id,current_user.user_id, payload)
    job_post = await get_job_post_by_id(db, job_id, version=update_data.version)
    job_data = {
        "job_id": str(job_post.job_id),
        "job_title": job_post.job_title,
        "job_description": job_post.description,
        "required_skills": job_post.required_skills,
        "preferred_skills": job_post.preferred_skills,
        "min_experience": job_post.min_experience,
        "max_experience": job_post.max_experience,
        "min_educational_qualifications": job_post.min_educational_qualifications,
        "location_preference": job_post.location_preference,
        "number_of_candidates_required": job_post.no_of_candidates_required,
        "version": job_post.version,
    }
    background_tasks.add_task(launch_scoring_agent, job_id, job_data)
    return JobPostResponse.model_validate(job_post)


async def close_job_post_service(
    db: AsyncSession, job_id: uuid.UUID, current_user
) -> JobPostCloseResponse:
    job_post = await get_job_post_by_id(db, job_id)
    if not job_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job post {job_id} not found.",
        )
    if job_post.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to close this job post.",
        )
    close_job = await close_job_post(db, job_id)
    return JobPostCloseResponse(job_id=str(job_post.job_id), status="Closed")


async def delete_all_job_posts_service(db: AsyncSession):
    job_posts = await get_all_job_posts(db)
    for job in job_posts:
        await delete_job_scores(db, job.job_id)
        await delete_job_shortlist(db, job.job_id)
        await delete_job_post(db, job.job_id)
