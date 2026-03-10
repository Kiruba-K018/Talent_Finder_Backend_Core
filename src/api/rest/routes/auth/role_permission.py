from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import requires_admin
from src.core.services.role_permission import role_permission_service
from src.data.clients.postgres_client import get_db
from src.schemas.auth_schema import (
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
async def get_all_roles(
    current_user=Depends(requires_admin), db: AsyncSession = Depends(get_db)
):
    roles = await role_permission_service.get_all_roles(db)
    return roles


@role_permission_router.get(
    "/roles/{role_id}", status_code=200, response_model=RoleResponse
)
async def get_role(
    role_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    role = await role_permission_service.get_role(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return role


@role_permission_router.post("/roles/", status_code=201, response_model=RoleResponse)
async def create_role(
    request: RoleRequest,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        role = await role_permission_service.create_new_role(db, request.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return role


@role_permission_router.delete("/roles/{role_id}", status_code=204)
async def delete_role(
    role_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    success = await role_permission_service.delete_role_by_id(db, role_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role not found"
        )
    return None


@role_permission_router.get(
    "/permissions/", status_code=200, response_model=list[PermissionResponse]
)
async def get_all_permissions(
    current_user=Depends(requires_admin), db: AsyncSession = Depends(get_db)
):
    permissions = await role_permission_service.get_all_permissions(db)
    return permissions


@role_permission_router.get(
    "/permissions/{permission_id}", status_code=200, response_model=PermissionResponse
)
async def get_permission(
    permission_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
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
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        permission = await role_permission_service.create_new_permission(
            db, request.entity_name, request.action
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return permission


@role_permission_router.delete("/permissions/{permission_id}", status_code=204)
async def delete_permission(
    permission_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    success = await role_permission_service.delete_permission_by_id(db, permission_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    return None


@role_permission_router.post(
    "/roles/{role_id}/permissions/{permission_id}", status_code=200
)
async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        mapping = await role_permission_service.assign_permission(
            db, role_id, permission_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"message": "Permission assigned to role successfully"}


@role_permission_router.delete(
    "/roles/{role_id}/permissions/{permission_id}", status_code=204
)
async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    success = await role_permission_service.remove_permission(
        db, role_id, permission_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found"
        )
    return None


@role_permission_router.get(
    "/roles/{role_id}/permissions/",
    status_code=200,
    response_model=list[PermissionResponse],
)
async def get_role_permissions(
    role_id: int,
    current_user=Depends(requires_admin),
    db: AsyncSession = Depends(get_db),
):
    permissions = await role_permission_service.get_role_permissions(db, role_id)
    return permissions

    pass
