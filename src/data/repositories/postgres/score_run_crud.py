import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.models.postgres.score_run_models import ScoreEvents, ScoreRuns
from src.schemas.score_run_schema import ScoreEventCreate, ScoreRunCreate


async def create_score_run(db: AsyncSession, data: ScoreRunCreate) -> ScoreRuns:
    try:
        score_run = ScoreRuns(
            job_id=data.job_id,
            job_version=data.job_version,
            triggered_by=data.triggered_by,
            status="queued",
        )
        db.add(score_run)
        await db.commit()
        await db.refresh(score_run)
        return score_run
    except Exception as e:
        await db.rollback()
        raise e


async def start_score_run(db: AsyncSession, score_run_id: uuid.UUID) -> None:
    try:
        stmt = (
            update(ScoreRuns)
            .where(ScoreRuns.score_run_id == score_run_id)
            .values(status="running", started_at=datetime.now(UTC))
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e


async def complete_score_run(db: AsyncSession, score_run_id: uuid.UUID) -> None:
    try:
        stmt = (
            update(ScoreRuns)
            .where(ScoreRuns.score_run_id == score_run_id)
            .values(status="completed", completed_at=datetime.now(UTC))
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e


async def fail_score_run(
    db: AsyncSession, score_run_id: uuid.UUID, error_message: str
) -> None:
    try:
        stmt = (
            update(ScoreRuns)
            .where(ScoreRuns.score_run_id == score_run_id)
            .values(
                status="failed",
                completed_at=datetime.now(UTC),
                error_message=error_message,
            )
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e


async def get_score_run(db: AsyncSession, score_run_id: uuid.UUID) -> ScoreRuns | None:
    result = await db.execute(
        select(ScoreRuns).where(ScoreRuns.score_run_id == score_run_id)
    )
    return result.scalars().first()


async def get_active_score_run(db: AsyncSession, job_id: uuid.UUID) -> ScoreRuns | None:
    result = await db.execute(
        select(ScoreRuns)
        .where(ScoreRuns.job_id == job_id, ScoreRuns.status.in_(["queued", "running"]))
        .order_by(ScoreRuns.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def create_score_event(db: AsyncSession, data: ScoreEventCreate) -> ScoreEvents:
    try:
        score_event = ScoreEvents(
            score_run_id=data.score_run_id,
            job_id=data.job_id,
            job_version=data.job_version,
            event=data.event,
            data=data.data,
        )
        db.add(score_event)
        await db.commit()
        await db.refresh(score_event)
        return score_event
    except Exception as e:
        await db.rollback()
        raise e


async def get_score_events_since(
    db: AsyncSession, score_run_id: uuid.UUID, last_seen_id: int
) -> list[ScoreEvents]:
    result = await db.execute(
        select(ScoreEvents)
        .where(
            ScoreEvents.score_run_id == score_run_id,
            ScoreEvents.event_id > last_seen_id,
        )
        .order_by(ScoreEvents.event_id.asc())
    )
    return result.scalars().all()


async def get_latest_score_event(
    db: AsyncSession, score_run_id: uuid.UUID
) -> int | None:
    result = await db.execute(
        select(func.max(ScoreEvents.event_id)).where(
            ScoreEvents.score_run_id == score_run_id
        )
    )
    return result.scalar()


async def delete_completed_events_for_run(
    db: AsyncSession, older_than_hours: int = 2
) -> int:
    try:
        threshold = datetime.now(UTC) - timedelta(hours=older_than_hours)

        subquery = select(ScoreRuns.score_run_id).where(
            ScoreRuns.status.in_(["completed", "failed"]),
            ScoreRuns.completed_at < threshold,
        )

        stmt = delete(ScoreEvents).where(ScoreEvents.score_run_id.in_(subquery))
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    except Exception as e:
        await db.rollback()
        raise e


async def delete_completed_runs(db: AsyncSession, older_than_hours: int = 2) -> int:
    try:
        threshold = datetime.now(UTC) - timedelta(hours=older_than_hours)

        stmt = delete(ScoreRuns).where(
            ScoreRuns.status.in_(["completed", "failed"]),
            ScoreRuns.completed_at < threshold,
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
    except Exception as e:
        await db.rollback()
        raise e
