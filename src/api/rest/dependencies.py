from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.auth.auth_service import verify_access_token
from src.data.clients.postgres_client import get_db
from src.data.models.postgres.auth_models import User
from src.data.repositories.postgres.role_crud import get_role_by_id
from src.data.repositories.postgres.user_crud import get_user_by_id

# OAuth2 password flow scheme with scopes for admin and recruiter routes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "admin": "Access to administrator-only endpoints",
        "recruiter": "Access to recruiter-only endpoints",
    },
)

# keep HTTPBearer for backwards compatibility if some legacy code still uses it
security = HTTPBearer()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    Validates current user from JWT:
    - Verifies token integrity
    - Cross-checks DB for user existence and active status
    - Optionally revalidates role/permission consistency
    """
    # Decode & verify JWT
    if not token:
        raise HTTPException(status_code=401, detail="Authorization token missing")
    try:
        payload = await verify_access_token(db, token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token or expired")

    user_id = payload.get("sub")
    token_role_id = payload.get("role_id", [])

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # --- Fetch user from DB ---
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_id(session=db, user_id=user_uuid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # --- Verify DB role still exists (protect against revoked roles) ---
    db_role = await get_role_by_id(session=db, role_id=user.role_id)
    if not db_role:
        raise HTTPException(status_code=403, detail="User role revoked")

    return user


async def requires_admin(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
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
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
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
