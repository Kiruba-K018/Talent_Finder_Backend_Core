from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.dependencies import get_db, requires_admin
from src.config.settings import setting
from src.core.services.source_run.sourcing_config_service import (
    create_sourcing_config_service,
    deactivate_sourcing_config_service,
    get_sourcing_config_service,
)
from src.data.models.postgres.auth_models import User
from src.schemas.sourcing_config_schema import (
    SourcingConfigCreate,
    SourcingConfigResponse,
)

sourcing_config_router = APIRouter(
    prefix="/api/v1/admin/sourcing-config", tags=["Sourcing Config"]
)
 

@sourcing_config_router.post(
    "/", response_model=SourcingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_sourcing_config(
    config_data: SourcingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_admin),
):
    """
    Create a new sourcing configuration for the organization.
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
    current_user: User = Depends(requires_admin),
):
    """
    Get the active sourcing configuration for the organization.
    """
    try:
        config = await get_sourcing_config_service(db, current_user.org_id)
        return config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@sourcing_config_router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_sourcing_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_admin),
):
    """
    Deactivate the active sourcing configuration for the organization.
    """
    try:
        await deactivate_sourcing_config_service(db, current_user.org_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@sourcing_config_router.put("/{config_id}", response_model=SourcingConfigResponse)
async def update_sourcing_config(
    config_id: str,
    config_data: SourcingConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_admin),
):
    """
    Update the active sourcing configuration for the organization.
    """
    try:
        config_dict = config_data.model_dump()
        updated_config = await create_sourcing_config_service(db, current_user.user_id, config_dict)
        return updated_config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))