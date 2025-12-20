from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import Identified


class ExportCreate(BaseModel):
    """Schema for creating a new export."""

    project_id: str
    topic_id: Optional[str] = None
    name: str = Field(..., max_length=255)
    format: str = Field(..., max_length=20)  # jsonl, csv, zip


class ExportRead(Identified):
    """Schema for reading export data."""

    project_id: str
    topic_id: Optional[str] = None
    name: str
    format: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    record_count: int
    status: str
    error_message: Optional[str] = None
