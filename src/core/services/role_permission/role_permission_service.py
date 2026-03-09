from sqlalchemy.ext.asyncio import AsyncSession
from src.data.repositories.postgres import role_crud


async def get_role(session: AsyncSession, role_id: int):
    return await role_crud.get_role_by_id(session, role_id)


async def get_role_by_name(session: AsyncSession, role_name: str):
    return await role_crud.get_role_by_name(session, role_name)


async def get_all_roles(session: AsyncSession):
    return await role_crud.get_all_roles(session)


async def create_new_role(session: AsyncSession, role_name: str):
    try:
        return await role_crud.create_role(session, role_name)
    except ValueError as e:
        raise e


async def delete_role_by_id(session: AsyncSession, role_id: int):
    return await role_crud.delete_role(session, role_id)


async def get_permission(session: AsyncSession, permission_id: int):
    return await role_crud.get_permission_by_id(session, permission_id)


async def get_all_permissions(session: AsyncSession):
    return await role_crud.get_all_permissions(session)


async def create_new_permission(
    session: AsyncSession,
    entity_name: str,
    action: str
):
    try:
        return await role_crud.create_permission(session, entity_name, action)
    except ValueError as e:
        raise e


async def delete_permission_by_id(session: AsyncSession, permission_id: int):
    return await role_crud.delete_permission(session, permission_id)


async def assign_permission(
    session: AsyncSession,
    role_id: int,
    permission_id: int
):
    try:
        return await role_crud.assign_permission_to_role(session, role_id, permission_id)
    except ValueError as e:
        raise e


async def remove_permission(
    session: AsyncSession,
    role_id: int,
    permission_id: int
):
    return await role_crud.remove_permission_from_role(session, role_id, permission_id)


async def get_role_permissions(session: AsyncSession, role_id: int):
    return await role_crud.get_role_permissions(session, role_id)
