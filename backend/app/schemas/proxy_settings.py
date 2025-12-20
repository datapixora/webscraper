"""
Pydantic schemas for proxy settings configuration.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProxySettings(BaseModel):
    """
    Schema for proxy configuration settings.
    All fields are optional to allow partial updates.
    """

    # Core proxy configuration
    proxy_enabled: bool = Field(default=False, description="Enable or disable proxy usage globally")
    proxy_provider: str = Field(
        default="smartproxy", description="Proxy provider name (e.g., smartproxy, bright data)"
    )
    proxy_type: str = Field(default="residential", description="Proxy type (residential, datacenter, mobile)")
    proxy_country: str = Field(default="us", description="Country code for geo-targeting (e.g., us, uk, de)")

    # Sticky session configuration
    proxy_sticky_enabled: bool = Field(default=False, description="Enable sticky sessions for consistent IP")
    proxy_sticky_ttl_sec: int = Field(
        default=300, description="TTL for sticky sessions in seconds (default 5 minutes)", ge=0, le=3600
    )

    # Rotation strategy
    proxy_rotation_strategy: Literal["per_job", "on_failure", "per_request"] = Field(
        default="per_job",
        description="When to rotate proxy: per_job (each job gets new IP), on_failure (rotate on 403/429/503), per_request (rotate every request)",
    )

    # Retry configuration
    proxy_retry_count: int = Field(
        default=3, description="Number of retries on proxy failure before giving up", ge=0, le=10
    )

    # Request delay configuration
    request_delay_min_ms: int = Field(
        default=500, description="Minimum delay between requests in milliseconds", ge=0, le=60000
    )
    request_delay_max_ms: int = Field(
        default=2000, description="Maximum delay between requests in milliseconds", ge=0, le=60000
    )

    # Scrape method policy
    scrape_method_policy: Literal["http", "browser", "auto"] = Field(
        default="auto",
        description="Scrape method: http (httpx only), browser (playwright only), auto (try http first, fallback to browser)",
    )


class ProxySettingsRead(ProxySettings):
    """Schema for reading proxy settings (includes all fields)."""

    pass


class ProxySettingsUpdate(BaseModel):
    """
    Schema for updating proxy settings.
    All fields are optional to allow partial updates.
    """

    proxy_enabled: Optional[bool] = None
    proxy_provider: Optional[str] = None
    proxy_type: Optional[str] = None
    proxy_country: Optional[str] = None
    proxy_sticky_enabled: Optional[bool] = None
    proxy_sticky_ttl_sec: Optional[int] = Field(None, ge=0, le=3600)
    proxy_rotation_strategy: Optional[Literal["per_job", "on_failure", "per_request"]] = None
    proxy_retry_count: Optional[int] = Field(None, ge=0, le=10)
    request_delay_min_ms: Optional[int] = Field(None, ge=0, le=60000)
    request_delay_max_ms: Optional[int] = Field(None, ge=0, le=60000)
    scrape_method_policy: Optional[Literal["http", "browser", "auto"]] = None
