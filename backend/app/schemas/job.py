from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.job import JobStatus
from app.schemas.base import Identified


class JobCreate(BaseModel):
    project_id: str
    topic_id: Optional[str] = None
    name: str = Field(..., max_length=255)
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = Field(default=None, max_length=255)
    target_url: str = Field(..., max_length=2048)


class JobBatchCreate(BaseModel):
    """
    Batch creation payload. Supports both legacy shape (project_id + urls)
    and a list of JobCreate items for forward compatibility.
    """

    jobs: Optional[list[JobCreate]] = None
    project_id: Optional[str] = None
    topic_id: Optional[str] = None
    urls: Optional[list[str]] = None
    name_prefix: Optional[str] = Field(default="Job", max_length=100)
    allow_duplicates: Optional[bool] = False

    @model_validator(mode="after")
    def validate_payload(self) -> "JobBatchCreate":
        if self.jobs:
            if len(self.jobs) == 0:
                raise ValueError("jobs must contain at least one item")
            project_ids = {j.project_id for j in self.jobs}
            if len(project_ids) != 1:
                raise ValueError("All jobs in batch must share the same project_id")
        elif self.project_id and self.urls:
            if len(self.urls) == 0:
                raise ValueError("urls must contain at least one item")
        else:
            raise ValueError("Provide either jobs[] or project_id + urls")
        return self


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class JobRead(Identified):
    project_id: str
    topic_id: Optional[str] = None
    name: str
    status: JobStatus
    target_url: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    error_message: Optional[str] = None
