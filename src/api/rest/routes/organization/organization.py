from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db, requires_admin
from src.core.services.organization import organization_service
from src.data.clients.postgres_client import get_db
from src.schemas.auth_schema import OrganizationRequest, OrganizationResponse, DeleteResponse

organization_router = APIRouter(prefix="/organizations")


@organization_router.post("/", status_code=201, response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    """Create a new organization.
    
    Only admin users can create organizations. Organization name must be unique.
    
    Args:
        request: OrganizationRequest containing org_name and org_logo.
        db: Database session for organization creation.
        current_user: Authenticated admin user.
    
    Returns:
        OrganizationResponse: Created organization with id and details.
    
    Raises:
        HTTPException: 400 if organization name already exists, 403 if not admin.
    """
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
    """Retrieve a specific organization by ID.
    
    Returns details of a specific organization including name and logo.
    
    Args:
        org_id: String ID of the organization.
        db: Database session for organization lookup.
    
    Returns:
        OrganizationResponse: Organization details.
    
    Raises:
        HTTPException: 404 if organization not found.
    """
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
    """Retrieve all organizations in the system.
    
    Returns complete list of all registered organizations.
    
    Args:
        db: Database session for organization queries.
    
    Returns:
        list[OrganizationResponse]: List of all organizations with details.
    """
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
    """Update organization details.
    
    Only admin users can update organizations. Updates name and logo.
    
    Args:
        org_id: String ID of the organization.
        request: OrganizationRequest with updated org_name and org_logo.
        db: Database session for update operation.
        current_user: Authenticated admin user.
    
    Returns:
        OrganizationResponse: Updated organization details.
    
    Raises:
        HTTPException: 404 if organization not found, 403 if not admin.
    """
    org = await organization_service.update_organization_details(
        db, org_id, org_name=request.org_name, org_logo=request.org_logo
    )

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return org


@organization_router.delete("/{org_id}", status_code=200, response_model=DeleteResponse)
async def delete_organization(
    org_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
)-> DeleteResponse:
    """Delete an organization.
    
    Only admin users can delete organizations. Organization must have no associated records.
    
    Args:
        org_id: String ID of the organization.
        db: Database session for deletion operation.
        current_user: Authenticated admin user.
    
    Returns:
        DeleteResponse: Confirmation message of deletion.
    
    Raises:
        HTTPException: 404 if organization not found, 403 if not admin.
    """
    success = await organization_service.delete_organization_by_id(db, org_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return DeleteResponse(message=f"Organization {org_id} deleted successfully")
