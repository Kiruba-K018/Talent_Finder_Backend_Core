import logging

from src.data.clients.postgres_client import get_session_factory
from src.data.repositories.postgres.score_run_crud import create_score_event
from src.schemas.score_run_schema import ScoreEventCreate

logger = logging.getLogger(__name__)


async def emit_score_event(data: ScoreEventCreate) -> None:
    try:
        session_factory = get_session_factory()
        async with session_factory() as db:
            await create_score_event(db, data)
    except Exception as e:
        logger.warning(
            f"Failed to emit score event for score_run_id {data.score_run_id}: {e}"
        )
