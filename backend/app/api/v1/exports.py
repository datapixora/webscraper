"""
API endpoints for managing data exports.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.export import ExportCreate, ExportRead
from app.services.exports import export_service
from app.services.export_generator import export_generator

router = APIRouter()


@router.get("/", response_model=list[ExportRead])
async def list_exports(
    project_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    export_status: Optional[str] = None,
    export_format: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[ExportRead]:
    """
    List all exports with optional filters.

    Query Parameters:
        project_id: Filter by project ID
        topic_id: Filter by topic ID
        export_status: Filter by status (pending, generating, ready, failed)
    """
    exports = await export_service.list(
        db,
        project_id=project_id,
        topic_id=topic_id,
        status=export_status,
        export_format=export_format,
        date_from=date_from,
        date_to=date_to,
    )
    return [ExportRead.model_validate(e) for e in exports]


@router.post("/", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
async def create_export(payload: ExportCreate, db: AsyncSession = Depends(get_db)) -> ExportRead:
    """
    Create a new export request.

    This creates an export record with status 'pending'.
    A background task should be triggered to generate the actual export file.
    """
    export = await export_service.create(db, payload)
    export = await export_generator.generate(db, export)
    return ExportRead.model_validate(export)


@router.get("/{export_id}", response_model=ExportRead)
async def get_export(export_id: str, db: AsyncSession = Depends(get_db)) -> ExportRead:
    """
    Get a specific export by ID.
    """
    export = await export_service.get(db, export_id)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export '{export_id}' not found")
    return ExportRead.model_validate(export)


@router.get("/{export_id}/download")
async def download_export(export_id: str, db: AsyncSession = Depends(get_db)) -> FileResponse:
    """
    Download the export file.

    Only available if export status is 'ready' and file_path is set.
    """
    export = await export_service.get(db, export_id)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export '{export_id}' not found")

    if export.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready for download. Current status: {export.status}",
        )

    if not export.file_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export file path is missing",
        )

    # Determine media type based on format
    media_type_map = {
        "jsonl": "application/x-ndjson",
        "csv": "text/csv",
        "zip": "application/zip",
    }
    # If the stored format doesn't match the file extension, trust the file extension
    fmt = export.format
    if export.file_path and export.file_path.lower().endswith(".zip"):
        fmt = "zip"
    media_type = media_type_map.get(fmt, "application/octet-stream")

    return FileResponse(
        path=export.file_path,
        media_type=media_type,
        filename=f"{export.name}.{fmt}",
    )


@router.post("/{export_id}/regenerate", response_model=ExportRead)
async def regenerate_export(export_id: str, db: AsyncSession = Depends(get_db)) -> ExportRead:
    """
    Regenerate a failed or existing export.

    Sets the export status back to 'pending' and triggers a new generation task.
    """
    export = await export_service.get(db, export_id)
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export '{export_id}' not found")

    # Reset export to pending status
    export = await export_service.update_status(
        db,
        export=export,
        status="pending",
        file_path=None,
        file_size=None,
        record_count=0,
        error_message=None,
    )

    export = await export_generator.generate(db, export)

    return ExportRead.model_validate(export)
