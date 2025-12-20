"""
Pydantic schemas for Setting model.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import Identified


class SettingCreate(BaseModel):
    key: str = Field(..., max_length=255)
    value: Optional[dict] = None
    description: Optional[str] = None
    category: str = Field(default="general", max_length=100)


class SettingUpdate(BaseModel):
    value: dict = Field(..., description="Setting value as JSON object")
    description: Optional[str] = None


class SettingRead(Identified):
    key: str
    value: Optional[dict] = None
    description: Optional[str] = None
    category: str
