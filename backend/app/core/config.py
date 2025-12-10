from functools import lru_cache
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
        default=["http://localhost:3000", "http://localhost:8000"],
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
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

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
