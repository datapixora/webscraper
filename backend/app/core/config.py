from functools import lru_cache
import json
from typing import List

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    environment: str = Field(default="development", alias="ENVIRONMENT")
    project_name: str = Field(default="WebScraper Platform", alias="PROJECT_NAME")
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")

    # CORS
    backend_cors_origins: List[str] = Field(
        default=["http://localhost:3002", "http://localhost:8000"],
        alias="CORS_ORIGINS",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://webscraper:webscraper_dev_password@localhost:5432/webscraper_db",
        alias="DATABASE_URL",
    )

    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_broker_url: str | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: str | None = Field(default=None, alias="CELERY_RESULT_BACKEND")
    celery_task_time_limit: int = Field(default=3600, alias="CELERY_TASK_TIME_LIMIT")

    # Scraper
    playwright_timeout_ms: int = Field(default=20000, alias="PLAYWRIGHT_TIMEOUT")
    http_timeout: float = Field(default=30.0, alias="DEFAULT_TIMEOUT")
    playwright_block_resources: bool = Field(default=True, alias="PLAYWRIGHT_BLOCK_RESOURCES")

    # SmartProxy Configuration
    smartproxy_enabled: bool = Field(default=False, alias="SMARTPROXY_ENABLED")
    smartproxy_host: str = Field(default="", alias="SMARTPROXY_HOST")
    smartproxy_port: int = Field(default=7000, alias="SMARTPROXY_PORT")
    smartproxy_username: str = Field(default="", alias="SMARTPROXY_USERNAME")
    smartproxy_password: str = Field(default="", alias="SMARTPROXY_PASSWORD")
    smartproxy_country: str = Field(default="", alias="SMARTPROXY_COUNTRY")

    # Storage
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./storage", alias="STORAGE_LOCAL_PATH")
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str | None = Field(default=None, alias="AWS_S3_BUCKET")
    aws_s3_region: str | None = Field(default=None, alias="AWS_S3_REGION")
    aws_s3_endpoint_url: str | None = Field(default=None, alias="AWS_S3_ENDPOINT_URL")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | List[str]) -> List[str]:
        default_origins = ["http://localhost:3002", "http://localhost:8000"]

        def merge_with_defaults(origins: list[str]) -> List[str]:
            merged: List[str] = []
            for origin in origins + default_origins:
                cleaned = origin.strip()
                if cleaned and cleaned not in merged:
                    merged.append(cleaned)
            return merged

        if isinstance(value, str):
            stripped = value.strip()
            if stripped in ("", "[]"):
                return default_origins

            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        cleaned = [str(origin).strip() for origin in parsed if str(origin).strip()]
                        return merge_with_defaults(cleaned)
                except json.JSONDecodeError:
                    pass

            cleaned = [origin.strip() for origin in stripped.split(",") if origin.strip()]
            return merge_with_defaults(cleaned)

        if isinstance(value, list):
            return merge_with_defaults([str(v) for v in value if str(v).strip()])

        return default_origins

    @field_validator("celery_broker_url", "celery_result_backend", mode="before")
    @classmethod
    def default_redis(cls, value: str | None, info: ValidationInfo) -> str:
        if value:
            return value
        redis_url = (info.data or {}).get("redis_url") if info else None
        return str(redis_url) if redis_url else "redis://localhost:6379/0"

    @property
    def async_database_url(self) -> str:
        """
        Ensure the SQLAlchemy async driver is used even if the env var omits it.
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
