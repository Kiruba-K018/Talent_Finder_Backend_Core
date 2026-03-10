from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.postgres import organization_crud


async def get_organization(session: AsyncSession, org_id: str):
    return await organization_crud.get_organization_by_id(session, org_id)


async def get_all_organizations(session: AsyncSession):
    return await organization_crud.get_all_organizations(session)


async def create_new_organization(
    session: AsyncSession, org_name: str, org_logo: str = None
):
    try:
        return await organization_crud.create_organization(
            session, org_name=org_name, org_logo=org_logo
        )
    except ValueError as e:
        raise e


async def update_organization_details(session: AsyncSession, org_id: str, **kwargs):
    return await organization_crud.update_organization(session, org_id, **kwargs)


async def delete_organization_by_id(session: AsyncSession, org_id: str):
    return await organization_crud.delete_organization(session, org_id)
