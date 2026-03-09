from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from src.data.models.postgres.auth_models import User
from datetime import datetime, timezone
import uuid 


async def get_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID):
    result = await session.execute(select(User).filter(User.user_id == user_id))
    return result.scalars().first()


async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()


async def create_user(
    session: AsyncSession,
    email: str,
    hashed_password: str,
    role_id: int,
    name: str = None,
    org_id: uuid.UUID = None
):
    try:
        user = User(
            user_id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            role_id=role_id,
            name=name,
            org_id=org_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError as e:
        await session.rollback()
        # uniqueness violation or other constraint
        raise ValueError(f"User with email '{email}' already exists or invalid data provided") from e
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"unable to create user: {e}") from e


async def update_user(session: AsyncSession, user_id: uuid.UUID, **kwargs):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"user with id '{user_id}' not found")
    
    for key, value in kwargs.items():
        if hasattr(user, key) and key != "user_id":
            setattr(user, key, value)
    
    user.updated_at = datetime.now(timezone.utc)
    try:
        await session.commit()
        await session.refresh(user)
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"failed to update user {user_id}: {e}") from e
    return user


async def delete_user(session: AsyncSession, user_id: uuid.UUID):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError(f"user with id '{user_id}' not found")
    try:
        await session.delete(user)
        await session.commit()
        return True
    except Exception as e:
        await session.rollback()
        raise RuntimeError(f"failed to delete user {user_id}: {e}") from e
