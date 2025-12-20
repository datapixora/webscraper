from datetime import datetime
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import Identified


class DomainPolicyBase(BaseModel):
    domain: str = Field(..., max_length=255, description="Bare domain, e.g. example.com")
    enabled: bool = True
    method: Literal["auto", "http", "playwright"] = "auto"
    use_proxy: bool = False
    request_delay_ms: int = 1000
    max_concurrency: int = 2
    user_agent: Optional[str] = Field(default=None, max_length=512)
    block_resources: bool = True

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        candidate = v.strip().lower()
        parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
        return parsed.hostname or candidate


class DomainPolicyCreate(DomainPolicyBase):
    pass


class DomainPolicyUpdate(BaseModel):
    enabled: Optional[bool] = None
    method: Optional[Literal["auto", "http", "playwright"]] = None
    use_proxy: Optional[bool] = None
    request_delay_ms: Optional[int] = None
    max_concurrency: Optional[int] = None
    user_agent: Optional[str] = None
    block_resources: Optional[bool] = None


class DomainPolicyRead(Identified, DomainPolicyBase):
    created_at: datetime
    updated_at: datetime
