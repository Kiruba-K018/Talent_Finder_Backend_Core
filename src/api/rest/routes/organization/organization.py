from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db, requires_admin
from src.core.services.organization import organization_service
from src.data.clients.postgres_client import get_db
from src.schemas.auth_schema import OrganizationRequest, OrganizationResponse

organization_router = APIRouter(prefix="/organizations")


@organization_router.post("/", status_code=201, response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    try:
        org = await organization_service.create_new_organization(
            db, org_name=request.org_name, org_logo=request.org_logo
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return org


@organization_router.get(
    "/{org_id}", status_code=200, response_model=OrganizationResponse
)
async def get_organization(org_id: str, db: AsyncSession = Depends(get_db)):
    org = await organization_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return org


@organization_router.get(
    "/", status_code=200, response_model=list[OrganizationResponse]
)
async def list_organizations(
    db: AsyncSession = Depends(get_db)
):
    orgs = await organization_service.get_all_organizations(db)
    return orgs


@organization_router.put(
    "/{org_id}", status_code=200, response_model=OrganizationResponse
)
async def update_organization(
    org_id: str,
    request: OrganizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    org = await organization_service.update_organization_details(
        db, org_id, org_name=request.org_name, org_logo=request.org_logo
    )

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return org


@organization_router.delete("/{org_id}", status_code=204)
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    success = await organization_service.delete_organization_by_id(db, org_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return None
