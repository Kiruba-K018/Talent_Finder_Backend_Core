from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from src.data.models.postgres.auth_models import Role, Permission, RolePermissionMap
from datetime import datetime, timezone


async def get_role_by_id(session: AsyncSession, role_id: int):
    result = await session.execute(select(Role.role).filter(Role.role_id == role_id))
    if result:
        return result.scalars().first().lower()
    return None


async def get_role_by_name(session: AsyncSession, role_name: str):
    result = await session.execute(select(Role).filter(Role.role == role_name))
    if result:
        return result.scalars().first()
    return None


async def get_all_roles(session: AsyncSession):
    result = await session.execute(select(Role))
    return result.scalars().all()


async def create_role(session: AsyncSession, role_name: str):
    try:
        role = Role(
            role=role_name,
            created_at=datetime.now(timezone.utc)
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role
    except IntegrityError as e:
        await session.rollback()
        raise ValueError(f"Role {role_name} already exists") from e


async def delete_role(session: AsyncSession, role_id: int):
    role = await get_role_by_id(session, role_id)
    if role:
        await session.delete(role)
        await session.commit()
        return True
    return False


async def get_permission_by_id(session: AsyncSession, permission_id: int):
    result = await session.execute(
        select(Permission).filter(Permission.permission_id == permission_id)
    )
    return result.scalars().first()


async def get_all_permissions(session: AsyncSession):
    result = await session.execute(select(Permission))
    return result.scalars().all()


async def create_permission(session: AsyncSession, entity_name: str, action: str):
    try:
        permission = Permission(
            entity_name=entity_name,
            action=action
        )
        session.add(permission)
        await session.commit()
        await session.refresh(permission)
        return permission
    except IntegrityError as e:
        await session.rollback()
        raise ValueError(f"Permission {entity_name} - {action} already exists") from e


async def delete_permission(session: AsyncSession, permission_id: int):
    permission = await get_permission_by_id(session, permission_id)
    if permission:
        await session.delete(permission)
        await session.commit()
        return True
    return False


async def assign_permission_to_role(
    session: AsyncSession,
    role_id: int,
    permission_id: int
):
    try:
        mapping = RolePermissionMap(
            role_id=role_id,
            permission_id=permission_id
        )
        session.add(mapping)
        await session.commit()
        return mapping
    except IntegrityError as e:
        await session.rollback()
        raise ValueError("Permission already assigned to role") from e


async def remove_permission_from_role(
    session: AsyncSession,
    role_id: int,
    permission_id: int
):
    result = await session.execute(
        select(RolePermissionMap).filter(
            RolePermissionMap.role_id == role_id,
            RolePermissionMap.permission_id == permission_id
        )
    )
    mapping = result.scalars().first()
    if mapping:
        await session.delete(mapping)
        await session.commit()
        return True
    return False


async def get_role_permissions(session: AsyncSession, role_id: int):
    result = await session.execute(
        select(Permission).join(RolePermissionMap).filter(
            RolePermissionMap.role_id == role_id
        )
    )
    return result.scalars().all()
