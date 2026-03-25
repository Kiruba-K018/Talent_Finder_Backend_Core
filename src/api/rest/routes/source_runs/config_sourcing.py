from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db, requires_admin
from src.config.settings import setting
from src.core.services.source_run.sourcing_config_service import (
    create_sourcing_config_service,
    deactivate_sourcing_config_service,
    get_sourcing_config_service,
    get_sourcing_config_by_id_service,

)
from src.data.models.postgres.auth_models import User
from src.schemas.sourcing_config_schema import (
    SourcingConfigCreate,
    SourcingConfigResponse,
    SourcingConfigDeleteResponse,
)

sourcing_config_router = APIRouter(
    prefix="/api/v1/admin/sourcing-config", tags=["Sourcing Config"]
)
 

@sourcing_config_router.post(
    "/", response_model=SourcingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_sourcing_config(
    config_data: SourcingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    """Create a new sourcing configuration.
    
    Only admin users can create sourcing configurations. Configuration applies to the organization.
    
    Args:
        config_data: SourcingConfigCreate containing configuration parameters.
        db: Database session for configuration creation.
        current_user: Authenticated admin user.
    
    Returns:
        SourcingConfigResponse: Created configuration with id and details.
    
    Raises:
        HTTPException: 400 for invalid configuration, 403 if not admin.
    """
    try:
        config_dict = config_data.model_dump()
        new_config = await create_sourcing_config_service(db, current_user.user_id, config_dict)
        return new_config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@sourcing_config_router.get("/", response_model=SourcingConfigResponse)
async def get_sourcing_config(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    """Retrieve the active sourcing configuration.
    
    Returns current active sourcing configuration for the organization.
    
    Args:
        db: Database session for configuration lookup.
        current_user: Authenticated admin user.
    
    Returns:
        SourcingConfigResponse: Active configuration details.
    
    Raises:
        HTTPException: 400 if no active configuration found, 403 if not admin.
    """
    try:
        config = await get_sourcing_config_service(db, current_user.org_id)
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sourcing_config_router.get("/{config_id}", response_model=SourcingConfigResponse)
async def get_sourcing_config_by_id(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    """Retrieve a specific sourcing configuration by ID.
    
    Returns details of a specific historical sourcing configuration.
    
    Args:
        config_id: String UUID of the configuration.
        db: Database session for configuration lookup.
        current_user: Authenticated admin user.
    
    Returns:
        SourcingConfigResponse: Configuration details.
    
    Raises:
        HTTPException: 400 if invalid format or config not found, 403 if not admin.
    """
    try:    
        config_id_uuid = UUID(config_id)
        config = await get_sourcing_config_by_id_service(db, config_id_uuid)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid config_id format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@sourcing_config_router.delete("/", status_code=status.HTTP_200_OK, response_model=SourcingConfigDeleteResponse)
async def deactivate_sourcing_config(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
)-> SourcingConfigDeleteResponse:
    """Deactivate the active sourcing configuration.
    
    Only admin users can deactivate configurations. Preserves configuration record in database.
    
    Args:
        db: Database session for update operation.
        current_user: Authenticated admin user.
    
    Returns:
        SourcingConfigDeleteResponse: Confirmation message of deactivation.
    
    Raises:
        HTTPException: 400 if no active configuration, 403 if not admin.
    """
    try:
        await deactivate_sourcing_config_service(db, current_user.org_id)
        return SourcingConfigDeleteResponse(message="Sourcing configuration deactivated successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@sourcing_config_router.put("/{config_id}", response_model=SourcingConfigResponse)
async def update_sourcing_config(
    config_id: str,
    config_data: SourcingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(requires_admin),
):
    """Update sourcing configuration.
    
    Only admin users can update configurations. Creates new configuration version.
    
    Args:
        config_id: String UUID of the configuration to update.
        config_data: SourcingConfigCreate with updated configuration parameters.
        db: Database session for update operation.
        current_user: Authenticated admin user.
    
    Returns:
        SourcingConfigResponse: Updated configuration with new version.
    
    Raises:
        HTTPException: 400 for invalid update, 403 if not admin.
    """
    try:
        config_dict = config_data.model_dump()
        updated_config = await create_sourcing_config_service(db, current_user.user_id, config_dict)
        return updated_config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))