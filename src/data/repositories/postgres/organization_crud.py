import uuid as python_uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.data.models.postgres.auth_models import Organization
from src.schemas.auth_schema import OrganizationResponse


async def get_organization_by_id(session: AsyncSession, org_id: str):
    result = await session.execute(
        select(Organization).filter(Organization.org_id == org_id)
    )
    return result.scalars().first()


async def get_all_organizations(session: AsyncSession):
    result = await session.execute(select(Organization))
    return result.scalars().all()


async def create_organization(
    session: AsyncSession, org_name: str, org_logo: str = None
):
    try:
        org = Organization(
            org_id=python_uuid.uuid4(),
            org_name=org_name,
            org_logo=org_logo,
            created_at=datetime.now(UTC),
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)
        return org
    except IntegrityError as e:
        await session.rollback()
        raise ValueError(f"Organization {org_name} already exists") from e


async def update_organization(session: AsyncSession, org_id: str, **kwargs):
    org = await get_organization_by_id(session, org_id)
    if not org:
        return None

    for key, value in kwargs.items():
        if hasattr(org, key) and key != "org_id":
            setattr(org, key, value)

    await session.commit()
    await session.refresh(org)
    return org


async def delete_organization(session: AsyncSession, org_id: str):
    org = await get_organization_by_id(session, org_id)
    if org:
        await session.delete(org)
        await session.commit()
        return True
    return False
