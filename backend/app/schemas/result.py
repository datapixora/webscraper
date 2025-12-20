from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.base import Identified


class ResultCreate(BaseModel):
    job_id: str
    project_id: str
    structured_data: Optional[dict[str, Any]] = None
    raw_html: Optional[str] = None  # preview/snippet
    raw_html_path: Optional[str] = None
    raw_html_checksum: Optional[str] = None
    raw_html_size: Optional[int] = None
    raw_html_compressed_size: Optional[int] = None
    http_status: Optional[int] = None
    blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    method_used: Optional[str] = None


class ResultRead(Identified):
    job_id: str
    project_id: str
    structured_data: Optional[dict[str, Any]] = None
    raw_html: Optional[str] = None  # preview/snippet
    raw_html_path: Optional[str] = None
    raw_html_checksum: Optional[str] = None
    raw_html_size: Optional[int] = None
    raw_html_compressed_size: Optional[int] = None
    http_status: Optional[int] = None
    blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    method_used: Optional[str] = None
