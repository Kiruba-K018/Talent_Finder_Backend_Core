import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.models.postgres.auth_models import RefreshToken, RevokedToken


async def create_refresh_token(
    session: AsyncSession, user_id: str, expires_at: datetime
):
    jti = uuid.uuid4()
    session_id = uuid.uuid4()

    token = RefreshToken(
        jti=jti,
        session_id=session_id,
        user_id=user_id,
        is_rotated=False,
        parent_jti=None,
        rotated_at=None,
        expires_at=expires_at,
        created_at=datetime.now(UTC),
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def get_refresh_token(session: AsyncSession, jti: str):
    result = await session.execute(select(RefreshToken).filter(RefreshToken.jti == jti))
    token = result.scalars().first()
    if not token:
        # caller may need to know it's missing
        raise ValueError(f"refresh token with jti {jti} not found")
    return token


async def get_refresh_token_by_user(session: AsyncSession, user_id: str):
    result = await session.execute(
        select(RefreshToken).filter(RefreshToken.user_id == user_id)
    )
    return result.scalars().all()


async def rotate_refresh_token(
    session: AsyncSession, old_jti: str, new_user_id: str, expires_at: datetime
):
    try:
        old_token = await get_refresh_token(session, old_jti)
    except ValueError:
        return None
    if not old_token:
        return None

    new_jti = uuid.uuid4()
    session_id = old_token.session_id

    new_token = RefreshToken(
        jti=new_jti,
        session_id=session_id,
        user_id=new_user_id,
        is_rotated=False,
        parent_jti=old_jti,
        rotated_at=datetime.now(UTC),
        expires_at=expires_at,
        created_at=datetime.now(UTC),
    )

    old_token.is_rotated = True
    old_token.rotated_at = datetime.now(UTC)

    session.add(new_token)
    await session.commit()
    await session.refresh(new_token)
    return new_token


async def revoke_refresh_token(session: AsyncSession, jti: str):
    try:
        token = await get_refresh_token(session, jti)
    except ValueError:
        # nothing to revoke
        return False
    if not token:
        return False

    revoked = RevokedToken(
        jti=jti, revoked_at=datetime.now(UTC), expires_at=token.expires_at
    )
    session.add(revoked)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"failed to revoke token {jti}: {e}") from e
    return True


async def is_token_revoked(session: AsyncSession, jti: str):
    result = await session.execute(select(RevokedToken).filter(RevokedToken.jti == jti))
    return result.scalars().first() is not None


async def delete_expired_tokens(session: AsyncSession):
    now = datetime.now(UTC)
    await session.execute(select(RefreshToken).filter(RefreshToken.expires_at < now))
    await session.execute(select(RevokedToken).filter(RevokedToken.expires_at < now))
    await session.commit()
