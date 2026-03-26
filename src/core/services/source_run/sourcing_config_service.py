import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.repositories.postgres.sourcing_config_crud import (
    create_or_update_sourcing_config,
    deactivate_sourcing_config,
    get_sourcing_config_by_id,
    get_sourcing_config_by_org,
)
from src.data.repositories.postgres.user_crud import get_user_by_id

logger = logging.getLogger(__name__)


async def create_sourcing_config_service(
    db: AsyncSession, current_user: uuid.UUID, config_data: dict
):
    """
    Create or update the sourcing configuration for the organization.
    """
    try:
        user = await get_user_by_id(db, current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        org_id = user.org_id
        config_data["org_id"] = org_id
        config_data["created_by"] = current_user

        existing_config = await get_sourcing_config_by_org(db, org_id)

        if existing_config:
            # Update existing config
            updated_config = await create_or_update_sourcing_config(db, config_data)
            return updated_config
        else:
            # Create new config
            new_config = await create_or_update_sourcing_config(db, config_data)
            return new_config
    except Exception as err:
        logger.error(f"Error creating/updating sourcing config: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        ) from err


async def get_sourcing_config_service(db: AsyncSession, org_id: uuid.UUID):
    """
    Retrieve the active sourcing configuration for the organization.
    """
    try:
        config = await get_sourcing_config_by_org(db, org_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sourcing configuration not found",
            )
        return config
    except Exception as err:
        logger.error(f"Error retrieving sourcing config: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        ) from err


async def get_sourcing_config_by_id_service(db: AsyncSession, config_id: uuid.UUID):
    """
    Retrieve a sourcing configuration by its ID.
    """
    try:
        config = await get_sourcing_config_by_id(db, config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sourcing configuration not found",
            )
        return config
    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"Error retrieving sourcing config by ID: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err)
        ) from err


async def deactivate_sourcing_config_service(db: AsyncSession, org_id: uuid.UUID):
    """
    Deactivate the active sourcing configuration for the organization.
    """
    try:
        await deactivate_sourcing_config(db, org_id)
    except Exception as err:
        logger.error(f"Error deactivating sourcing config: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
        ) from err
