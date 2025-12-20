"""
API endpoints for admin settings management (proxy, etc).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.proxy_settings import ProxySettings, ProxySettingsRead, ProxySettingsUpdate
from app.services.settings import setting_service

router = APIRouter()

PROXY_SETTINGS_KEY = "proxy_config"


@router.get("/proxy", response_model=ProxySettingsRead)
async def get_proxy_settings(db: AsyncSession = Depends(get_db)) -> ProxySettingsRead:
    """
    Get current proxy settings from database.
    Returns default values if not configured.
    """
    setting = await setting_service.get_by_key(db, PROXY_SETTINGS_KEY)

    if not setting or not setting.value:
        # Return defaults
        defaults = ProxySettings()
        return ProxySettingsRead(**defaults.model_dump())

    # Return stored settings
    return ProxySettingsRead(**setting.value)


@router.put("/proxy", response_model=ProxySettingsRead)
async def update_proxy_settings(
    payload: ProxySettingsUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProxySettingsRead:
    """
    Update proxy settings in database (upsert).
    Allows partial updates - only provided fields will be updated.
    """
    # Get current settings or defaults
    existing_setting = await setting_service.get_by_key(db, PROXY_SETTINGS_KEY)

    if existing_setting and existing_setting.value:
        # Start with existing values
        current_data = ProxySettings(**existing_setting.value)
    else:
        # Start with defaults
        current_data = ProxySettings()

    # Apply updates (only non-None fields from payload)
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(current_data, key, value)

    # Upsert to database
    updated_setting = await setting_service.upsert(
        db,
        key=PROXY_SETTINGS_KEY,
        value=current_data.model_dump(),
        description="Proxy and scraping configuration settings",
        category="proxy",
    )

    return ProxySettingsRead(**updated_setting.value)
