"""
Service layer for managing application settings stored in the database.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.schemas.setting import SettingCreate, SettingUpdate


class SettingService:
    """Service for managing application settings."""

    @staticmethod
    async def get_by_key(db: AsyncSession, key: str) -> Optional[Setting]:
        """
        Get a setting by its key.

        Args:
            db: Database session
            key: Setting key

        Returns:
            Setting object or None if not found
        """
        result = await db.execute(select(Setting).where(Setting.key == key))
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert(
        db: AsyncSession,
        key: str,
        value: dict,
        description: Optional[str] = None,
        category: str = "general",
    ) -> Setting:
        """
        Update existing setting or create new one.

        Args:
            db: Database session
            key: Setting key
            value: Setting value (JSON object)
            description: Optional description
            category: Setting category (default: "general")

        Returns:
            Updated or created Setting object
        """
        existing = await SettingService.get_by_key(db, key)

        if existing:
            # Update existing setting
            existing.value = value
            if description is not None:
                existing.description = description
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Create new setting
            new_setting = Setting(
                key=key,
                value=value,
                description=description,
                category=category,
            )
            db.add(new_setting)
            await db.commit()
            await db.refresh(new_setting)
            return new_setting

    @staticmethod
    async def create(db: AsyncSession, payload: SettingCreate) -> Setting:
        """
        Create a new setting.

        Args:
            db: Database session
            payload: Setting creation data

        Returns:
            Created Setting object
        """
        setting = Setting(
            key=payload.key,
            value=payload.value,
            description=payload.description,
            category=payload.category,
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
        return setting

    @staticmethod
    async def update(
        db: AsyncSession,
        setting: Setting,
        payload: SettingUpdate,
    ) -> Setting:
        """
        Update an existing setting.

        Args:
            db: Database session
            setting: Setting object to update
            payload: Update data

        Returns:
            Updated Setting object
        """
        setting.value = payload.value
        if payload.description is not None:
            setting.description = payload.description
        await db.commit()
        await db.refresh(setting)
        return setting

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Setting]:
        """
        List all settings.

        Args:
            db: Database session

        Returns:
            List of all Setting objects
        """
        result = await db.execute(select(Setting).order_by(Setting.category, Setting.key))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, setting: Setting) -> None:
        """
        Delete a setting.

        Args:
            db: Database session
            setting: Setting object to delete
        """
        await db.delete(setting)
        await db.commit()


# Singleton instance
setting_service = SettingService()
