import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.postgres.job_post_models import JobPostModel
from src.schemas.job_post_schema import JobPostCreate, JobPostUpdate, JobPostResponse


async def get_all_job_posts(db: AsyncSession) -> list[JobPostModel]:
    result = await db.execute(select(JobPostModel))
    return result.scalars().all()


async def get_job_post_by_id(
    db: AsyncSession, job_id: uuid.UUID, version: int | None = None
) -> JobPostModel | None:
    if version is None:
        result = await db.execute(select(JobPostModel).where(JobPostModel.job_id == job_id))
    else:
        result = await db.execute(select(JobPostModel).where(
            JobPostModel.job_id == job_id,
            JobPostModel.version == version
        ))
    return result.scalar_one_or_none()


async def create_job_post(db: AsyncSession, payload: JobPostCreate) -> JobPostModel:
    job_post = JobPostModel(
        job_id=uuid.uuid4(),
        job_title=payload.job_title,
        description=payload.job_description,
        min_experience=payload.min_experience,
        max_experience=payload.max_experience,
        min_educational_qualifications=",".join(payload.min_education_qualifications),
        job_type=payload.job_type,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        location_preference=payload.location_preference,
        no_of_candidates_required=payload.no_of_candidates_required,
        created_by=payload.created_by,
        status="created",
        version=1,
        created_at=datetime.now(),
    )
    db.add(job_post)
    await db.commit()
    await db.refresh(job_post)
    return job_post


async def update_job_post(
    db: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: JobPostUpdate,
) -> JobPostModel | None:
    job_post = await get_job_post_by_id(db, job_id)
    if not job_post:
        return None

    update_data = payload.model_dump(exclude_none=True)

    if "job_description" in update_data:
        update_data["description"] = update_data.pop("job_description")

    if "min_education_qualifications" in update_data:
        update_data["min_educational_qualifications"] = ",".join(
            update_data.pop("min_education_qualifications")
        )
    
    update_data["job_id"] = job_id
    update_data["updated_at"] = datetime.now()
    update_data["updated_by"] = user_id
    update_data["version"] = job_post.version + 1
    update_data["status"] = "created"

    await db.execute(
        update(JobPostModel).where(JobPostModel.job_id == job_id).values(**update_data)
    )
    await db.commit()
    await db.refresh(job_post)
    return job_post


async def close_job_post(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> JobPostModel | None:
    job_post = await get_job_post_by_id(db, job_id)
    if not job_post:
        return None

    if job_post.status == "Closed":
        return job_post

    await db.execute(
        update(JobPostModel)
        .where(JobPostModel.job_id == job_id)
        .values(
            status="Closed",
            updated_at=datetime.now(),
        )
    )
    await db.commit()
    await db.refresh(job_post)
    return job_post


async def update_job_post_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    new_status: str,
) -> bool:
    """Update job post status and updated_at timestamp."""
    try:
        await db.execute(
            update(JobPostModel)
            .where(JobPostModel.job_id == job_id)
            .values(
                status=new_status,
                updated_at=datetime.now(),
            )
        )
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        return False


async def delete_job_post(db: AsyncSession, job_id: uuid.UUID) -> None:
    try:
        job_post = await get_job_post_by_id(db, job_id)
        if job_post:
            await db.delete(job_post)
            await db.commit()
    except Exception as e:
        raise Exception(f"Failed to delete job post {job_id}") from e
