from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import requires_admin
from src.core.services.users import user_service
from src.data.clients.postgres_client import get_db
from src.schemas.auth_schema import CreateUserRequest, UserResponse, UserUpdate

users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@users_router.post("/", status_code=201, response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_admin=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    existing_user = await user_service.get_user_profile(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    try:
        user = await user_service.create_new_user(
            db,
            email=request.email,
            password=request.password,
            role_id=request.role_id,
            name=request.name,
            org_id=request.org_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return user


@users_router.get("/", response_model=list[UserResponse])
async def list_users(
    current_user=Depends(requires_admin), db: AsyncSession = Depends(get_db)
):
    users = await user_service.get_all_users(db)
    return users


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_details(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    user = await user_service.update_user_profile(db, user_id, **update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user
