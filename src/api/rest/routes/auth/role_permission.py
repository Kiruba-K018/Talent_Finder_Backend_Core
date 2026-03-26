from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import _admin_user, _db
from src.core.services.role_permission import role_permission_service
from src.schemas.auth_schema import (
    DeleteResponse,
    MessageResponse,
    PermissionRequest,
    PermissionResponse,
    RoleRequest,
    RoleResponse,
)

role_permission_router = APIRouter(
    prefix="/api/v1/role-permission", tags=["Role Permission"]
)


@role_permission_router.get(
    "/roles/", status_code=200, response_model=list[RoleResponse]
)
async def get_all_roles(db: AsyncSession = _db):
    """Retrieve all available roles in the system.

    Returns complete list of all roles that can be assigned to users.

    Args:
        db: Database session for role queries.

    Returns:
        list[RoleResponse]: List of all available roles with metadata.
    """
    roles = await role_permission_service.get_all_roles(db)
    return roles


@role_permission_router.get(
    "/roles/{role_id}", status_code=200, response_model=RoleResponse
)
async def get_role(
    role_id: int,
    db: AsyncSession = _db,
):
    """Retrieve specific role by ID.

    Returns details of a specific role including creation timestamp.

    Args:
        role_id: Numeric ID of the role.
        db: Database session for role lookup.

    Returns:
        RoleResponse: Role details with id, name, and metadata.

    Raises:
        HTTPException: 404 if role not found.
    """
    role = await role_permission_service.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return role


@role_permission_router.post("/roles/", status_code=201, response_model=RoleResponse)
async def create_role(
    request: RoleRequest,
    db: AsyncSession = _db,
    current_user=_admin_user,
):
    """Create a new role in the system.

    Requires admin privileges. Role name must be unique.

    Args:
        request: RoleRequest containing role name.
        db: Database session for role creation.
        current_user: Authenticated admin user.

    Returns:
        RoleResponse: Created role with id and metadata.

    Raises:
        HTTPException: 400 if role already exists.
        HTTPException: 403 if current user is not admin.
    """
    try:
        role = await role_permission_service.create_new_role(db, request.role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return role


@role_permission_router.delete(
    "/roles/{role_id}", status_code=200, response_model=DeleteResponse
)
async def delete_role(
    role_id: int,
    db: AsyncSession = _db,
    current_user=_admin_user,
) -> DeleteResponse:
    """Delete a role from the system.

    Requires admin privileges. Role must not be assigned to any users.

    Args:
        role_id: Numeric ID of role to delete.
        db: Database session for role deletion.
        current_user: Authenticated admin user.

    Returns:
        DeleteResponse: Confirmation message of deletion.

    Raises:
        HTTPException: 404 if role not found.
        HTTPException: 403 if current user is not admin.
    """
    success = await role_permission_service.delete_role_by_id(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return DeleteResponse(message=f"Role {role_id} deleted successfully")


@role_permission_router.get(
    "/permissions/", status_code=200, response_model=list[PermissionResponse]
)
async def get_all_permissions(db: AsyncSession = _db):
    """Retrieve all available permissions in the system.

    Returns complete list of all permissions that can be assigned to roles.

    Args:
        db: Database session for permission queries.

    Returns:
        list[PermissionResponse]: List of all available permissions.
    """
    permissions = await role_permission_service.get_all_permissions(db)
    return permissions


@role_permission_router.get(
    "/permissions/{permission_id}", status_code=200, response_model=PermissionResponse
)
async def get_permission(
    permission_id: int,
    db: AsyncSession = _db,
):
    """Retrieve specific permission by ID.

    Returns details of a specific permission including entity and action.

    Args:
        permission_id: Numeric ID of the permission.
        db: Database session for permission lookup.

    Returns:
        PermissionResponse: Permission details.

    Raises:
        HTTPException: 404 if permission not found.
    """
    permission = await role_permission_service.get_permission(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    return permission


@role_permission_router.post(
    "/permissions/", status_code=201, response_model=PermissionResponse
)
async def create_permission(
    request: PermissionRequest,
    db: AsyncSession = _db,
    current_user=_admin_user,
):
    """Create a new permission for entity and action.

    Only admin users can create new permissions. Validates unique
    entity-action combination.

    Args:
        request: PermissionRequest containing entity_name and action.
        db: Database session for permission creation.
        current_user: Authenticated user (must be admin).

    Returns:
        PermissionResponse: Created permission details.

    Raises:
        HTTPException: 400 if permission already exists, 403 if not admin.
    """
    try:
        permission = await role_permission_service.create_new_permission(
            db, request.entity_name, request.action
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return permission


@role_permission_router.delete(
    "/permissions/{permission_id}", status_code=200, response_model=DeleteResponse
)
async def delete_permission(
    permission_id: int,
    db: AsyncSession = _db,
    current_user=_admin_user,
) -> DeleteResponse:
    """Delete a permission from the system.

    Requires admin privileges. Permission must not be assigned to any roles.

    Args:
        permission_id: Numeric ID of permission to delete.
        db: Database session for permission deletion.
        current_user: Authenticated admin user.

    Returns:
        DeleteResponse: Confirmation message of deletion.

    Raises:
        HTTPException: 404 if permission not found, 403 if not admin.
    """
    success = await role_permission_service.delete_permission_by_id(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    return DeleteResponse(message=f"Permission {permission_id} deleted successfully")


@role_permission_router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=200,
    response_model=MessageResponse,
)
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: AsyncSession = _db,
    current_user=_admin_user,
) -> MessageResponse:
    """Assign a permission to a role.

    Only admin users can assign permissions to roles. Creates mapping
    between role and permission.

    Args:
        role_id: Numeric ID of the role.
        permission_id: Numeric ID of the permission to assign.
        db: Database session for assignment operation.
        current_user: Authenticated admin user.

    Returns:
        MessageResponse: Confirmation of permission assignment.

    Raises:
        HTTPException: 400 if assignment already exists, 403 if not admin.
    """
    try:
        await role_permission_service.assign_permission(db, role_id, permission_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    return MessageResponse(message="Permission assigned to role successfully")


@role_permission_router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    status_code=200,
    response_model=DeleteResponse,
)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: AsyncSession = _db,
    current_user=_admin_user,
) -> DeleteResponse:
    """Remove a permission from a role.

    Only admin users can remove permissions from roles. Deletes mapping
    between role and permission.

    Args:
        role_id: Numeric ID of the role.
        permission_id: Numeric ID of the permission to remove.
        db: Database session for removal operation.
        current_user: Authenticated admin user.

    Returns:
        DeleteResponse: Confirmation of permission removal.

    Raises:
        HTTPException: 404 if role or permission not found, 403 if not admin.
    """
    success = await role_permission_service.remove_permission(
        db, role_id, permission_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found"
        )
    return DeleteResponse(message="Permission removed from role successfully")


@role_permission_router.get(
    "/roles/{role_id}/permissions/",
    status_code=200,
    response_model=list[PermissionResponse],
)
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = _db,
):
    """Retrieve all permissions assigned to a specific role.

    Returns complete list of permissions that have been assigned to the given role.

    Args:
        role_id: Numeric ID of the role.
        db: Database session for permission queries.

    Returns:
        list[PermissionResponse]: List of permissions assigned to the role.
    """
    permissions = await role_permission_service.get_role_permissions(db, role_id)
    return permissions

    pass
