from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import Identified


class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    extraction_schema: Optional[dict] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    extraction_schema: Optional[dict] = None


class ProjectRead(Identified):
    name: str
    description: Optional[str] = None
    extraction_schema: Optional[dict] = None
