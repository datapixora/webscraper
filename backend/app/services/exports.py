"""
Service layer for managing export file generation and storage.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import Export, ExportStatus
from app.schemas.export import ExportCreate


class ExportService:
    """Service for managing data exports."""

    @staticmethod
    async def create(db: AsyncSession, payload: ExportCreate) -> Export:
        """
        Create a new export record.

        Args:
            db: Database session
            payload: Export creation data

        Returns:
            Created Export object
        """
        export = Export(
            project_id=payload.project_id,
            topic_id=payload.topic_id,
            name=payload.name,
            format=payload.format,
            status=ExportStatus.PENDING,
        )
        db.add(export)
        await db.commit()
        await db.refresh(export)
        return export

    @staticmethod
    async def list(
        db: AsyncSession,
        project_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        status: Optional[str] = None,
        export_format: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[Export]:
        """
        List exports with optional filters.

        Args:
            db: Database session
            project_id: Optional filter by project ID
            topic_id: Optional filter by topic ID
            status: Optional filter by status

        Returns:
            List of Export objects matching the filters
        """
        query = select(Export)

        if project_id is not None:
            query = query.where(Export.project_id == project_id)

        if topic_id is not None:
            query = query.where(Export.topic_id == topic_id)

        if status is not None:
            query = query.where(Export.status == status)
        if export_format is not None:
            query = query.where(Export.format == export_format)
        from datetime import datetime

        if date_from is not None:
            try:
                dt_from = datetime.fromisoformat(date_from)
                query = query.where(Export.created_at >= dt_from)
            except ValueError:
                pass
        if date_to is not None:
            try:
                dt_to = datetime.fromisoformat(date_to)
                query = query.where(Export.created_at <= dt_to)
            except ValueError:
                pass

        query = query.order_by(Export.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, export_id: str) -> Optional[Export]:
        """
        Get an export by ID.

        Args:
            db: Database session
            export_id: Export ID

        Returns:
            Export object or None if not found
        """
        result = await db.execute(select(Export).where(Export.id == export_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        export: Export,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        record_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Export:
        """
        Update export status and file information.

        Args:
            db: Database session
            export: Export object to update
            status: New status
            file_path: Optional file path
            file_size: Optional file size in bytes
            record_count: Number of records in export
            error_message: Optional error message if failed

        Returns:
            Updated Export object
        """
        export.status = status

        if file_path is not None:
            export.file_path = file_path

        if file_size is not None:
            export.file_size = file_size

        if record_count is not None:
            export.record_count = record_count

        if error_message is not None:
            export.error_message = error_message

        await db.commit()
        await db.refresh(export)
        return export

    @staticmethod
    async def delete(db: AsyncSession, export: Export) -> None:
        """
        Delete an export.

        Args:
            db: Database session
            export: Export object to delete
        """
        await db.delete(export)
        await db.commit()


# Singleton instance
export_service = ExportService()
