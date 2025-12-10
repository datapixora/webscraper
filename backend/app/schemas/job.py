from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.job import JobStatus
from app.schemas.base import Identified


class JobCreate(BaseModel):
    project_id: str
    name: str = Field(..., max_length=255)
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = Field(default=None, max_length=255)
    target_url: str = Field(..., max_length=2048)


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class JobRead(Identified):
    project_id: str
    name: str
    status: JobStatus
    target_url: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    error_message: Optional[str] = None
