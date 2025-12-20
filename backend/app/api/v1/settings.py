"""
API endpoints for managing application settings.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.db.session import get_db
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate
from app.services.settings import setting_service

router = APIRouter()


@router.get("/", response_model=list[SettingRead])
async def list_settings(db: AsyncSession = Depends(get_db)) -> list[SettingRead]:
    """
    List all settings stored in the database.
    """
    settings_list = await setting_service.list_all(db)
    return [SettingRead.model_validate(s) for s in settings_list]


@router.get("/{key}", response_model=SettingRead)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)) -> SettingRead:
    """
    Get a specific setting by key.

    If the setting doesn't exist in the database, returns default values from
    environment configuration for known keys like 'smartproxy'.
    """
    setting = await setting_service.get_by_key(db, key)

    if not setting:
        # For smartproxy key, return defaults from environment if not in DB
        if key == "smartproxy":
            default_value = {
                "enabled": app_settings.smartproxy_enabled,
                "host": app_settings.smartproxy_host,
                "port": app_settings.smartproxy_port,
                "username": app_settings.smartproxy_username,
                "password": app_settings.smartproxy_password,
                "country": app_settings.smartproxy_country,
            }
            # Return a pseudo-setting (not persisted)
            from datetime import datetime

            return SettingRead(
                id="",
                key=key,
                value=default_value,
                description="SmartProxy configuration (from environment)",
                category="proxy",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found")

    return SettingRead.model_validate(setting)


@router.post("/", response_model=SettingRead, status_code=status.HTTP_201_CREATED)
async def create_setting(payload: SettingCreate, db: AsyncSession = Depends(get_db)) -> SettingRead:
    """
    Create a new setting.
    """
    # Check if setting with this key already exists
    existing = await setting_service.get_by_key(db, payload.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Setting with key '{payload.key}' already exists. Use PATCH to update.",
        )

    setting = await setting_service.create(db, payload)
    return SettingRead.model_validate(setting)


@router.patch("/{key}", response_model=SettingRead)
async def update_setting(
    key: str,
    payload: SettingUpdate,
    db: AsyncSession = Depends(get_db),
) -> SettingRead:
    """
    Update or create a setting (upsert operation).

    If the setting exists, it will be updated.
    If it doesn't exist, a new setting will be created.
    """
    setting = await setting_service.upsert(
        db,
        key=key,
        value=payload.value,
        description=payload.description,
    )
    return SettingRead.model_validate(setting)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(key: str, db: AsyncSession = Depends(get_db)) -> None:
    """
    Delete a setting by key.
    """
    setting = await setting_service.get_by_key(db, key)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{key}' not found")

    await setting_service.delete(db, setting)
