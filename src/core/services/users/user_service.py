from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.auth_service import hash_password
from src.core.services.email_service import send_credentials_email
from src.data.repositories.postgres import role_crud, user_crud


async def create_new_user(
    session: AsyncSession,
    email: str,
    password: str,
    role_id: int,
    name: str = None,
    org_id: UUID = None,
):
    hashed_pwd = hash_password(password)

    try:
        user = await user_crud.create_user(
            session,
            email=email,
            hashed_password=hashed_pwd,
            role_id=role_id,
            name=name,
            org_id=org_id,
        )

        # send credentials email asynchronously; failures are logged
        try:
            await send_credentials_email(email, password, to=email)
        except Exception as e:
            raise e

        return user
    except ValueError as e:
        # propagate with context so route handlers can map to HTTP errors
        raise ValueError(f"failed to create user: {e}") from e
    except Exception as e:
        # catch-all so unexpected db errors bubble up with information
        raise RuntimeError(f"unexpected error creating user: {e}") from e


async def get_user_details(session: AsyncSession, user_id: UUID):
    return await user_crud.get_user_by_id(session, user_id)


async def get_user_profile(session: AsyncSession, email: str):
    return await user_crud.get_user_by_email(session, email)


async def get_all_users(session: AsyncSession):
    return await user_crud.get_all_users(session)


async def update_user_profile(session: AsyncSession, user_id: UUID, **kwargs):
    return await user_crud.update_user(session, user_id, **kwargs)


async def is_admin(session: AsyncSession, user_id: UUID):
    user = await user_crud.get_user_by_id(session, user_id)
    if not user:
        return False

    role = await role_crud.get_role_by_id(session, user.role_id)
    return role and role.role == "Admin"


async def is_recruiter(session: AsyncSession, user_id: UUID):
    user = await user_crud.get_user_by_id(session, user_id)
    if not user:
        return False

    role = await role_crud.get_role_by_id(session, user.role_id)
    return role and role.role.lower() == "recruiter"


async def get_current_user_profile_service(current_user, db):
    role = await role_crud.get_role_by_id(db, current_user.role_id)
    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "name": current_user.name,
        "role_id": role,
        "org_id": str(current_user.org_id) if current_user.org_id else None,
    }
