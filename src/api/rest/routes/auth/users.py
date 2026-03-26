from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import _admin_user, _db
from src.core.services.users import user_service
from src.schemas.auth_schema import CreateUserRequest, UserResponse, UserUpdate

users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@users_router.post("/", status_code=201, response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    db: AsyncSession = _db,
    current_user=_admin_user,
):
    """Create a new user account in the system.

    Requires admin privileges. Validates that email is unique and password
    meets security requirements before creating the user.

    Args:
        request: CreateUserRequest containing email, password, name, role_id, org_id.
        db: Database session for user creation.
        current_user: Authenticated admin user with creation permission.

    Returns:
        UserResponse: Created user details including user_id and metadata.

    Raises:
        HTTPException: 400 if email already registered or password invalid.
        HTTPException: 403 if current user is not admin.
    """
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
async def list_users(db: AsyncSession = _db):
    """Retrieve list of all users in the system.

    Returns paginated list of all registered users with their details.

    Args:
        db: Database session for user queries.

    Returns:
        list[UserResponse]: List of all users in the system.
    """
    users = await user_service.get_all_users(db)
    return users


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = _db,
):
    """Retrieve specific user details by user ID.

    Returns complete profile information for a specific user.

    Args:
        user_id: UUID of the user to retrieve.
        db: Database session for user lookup.

    Returns:
        UserResponse: User details including id, email, name, role, org.

    Raises:
        HTTPException: 404 if user not found.
    """
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
    db: AsyncSession = _db,
    current_user=_admin_user,
):
    """Update user profile information.

    Requires admin privileges. Updates only provided fields, leaving others unchanged.

    Args:
        user_id: UUID of user to update.
        updates: UserUpdate object with fields to update.
        db: Database session for user update.
        current_user: Authenticated admin user with update permission.

    Returns:
        UserResponse: Updated user details.

    Raises:
        HTTPException: 404 if user not found.
        HTTPException: 403 if current user is not admin.
    """
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    user = await user_service.update_user_profile(db, user_id, **update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user
