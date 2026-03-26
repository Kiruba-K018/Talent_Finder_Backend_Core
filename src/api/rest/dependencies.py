from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.auth_service import verify_access_token
from src.core.utils.background_task_manager import get_background_task_manager
from src.data.clients.mongodb_client import get_db as get_mongodb_db
from src.data.clients.postgres_client import get_db
from src.data.models.postgres.auth_models import User
from src.data.repositories.postgres.role_crud import get_role_by_id
from src.data.repositories.postgres.user_crud import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "admin": "Access to administrator-only endpoints",
        "recruiter": "Access to recruiter-only endpoints",
    },
)

security = HTTPBearer()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates current user from JWT:
    - Verifies token integrity
    - Cross-checks DB for user existence and active status
    - Optionally revalidates role/permission consistency
    """
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")
    try:
        payload = await verify_access_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token or expired") from e

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid token payload") from e

    user = await get_user_by_id(session=db, user_id=user_uuid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    db_role = await get_role_by_id(session=db, role_id=user.role_id)
    if not db_role:
        raise HTTPException(status_code=403, detail="User role revoked")

    return user


async def requires_admin(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Async dependency to ensure the current user has admin privileges.
    Raises HTTP 403 if the user is not an admin.
    """
    role = await get_role_by_id(session=db, role_id=user.role_id)
    if not role or role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return user


async def requires_recruiter(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Async dependency to ensure the current user has recruiter privileges.
    Raises HTTP 403 if the user is not a recruiter.
    """
    role = await get_role_by_id(session=db, role_id=user.role_id)
    if not role or role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter privileges required",
        )
    return user


_db: AsyncSession = Depends(get_db)
_current_user: User = Depends(get_current_user)
_admin_user: User = Depends(requires_admin)
_recruiter_user: User = Depends(requires_recruiter)
_mongodb = Depends(get_mongodb_db)


def get_background_task_manager_dep():
    """
    Dependency to get the background task manager instance.
    Can be injected into route handlers to schedule background tasks.
    """
    return get_background_task_manager()
