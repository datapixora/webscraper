from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.schemas.base import Identified


class DomainPolicyBase(BaseModel):
    domain: str = Field(..., max_length=255)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class DomainPolicyCreate(DomainPolicyBase):
    pass


class DomainPolicyUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict[str, Any]] = None


class DomainPolicyRead(Identified, DomainPolicyBase):
    created_at: datetime
    updated_at: datetime

