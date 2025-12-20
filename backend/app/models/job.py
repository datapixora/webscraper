from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as PgEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        PgEnum(
            JobStatus,
            name="job_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],  # ensure DB uses enum values
        ),
        default=JobStatus.PENDING,
        nullable=False,
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cron_expression: Mapped[str | None] = mapped_column(String(255))
    error_message: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="jobs")
    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="jobs")
    result: Mapped[Optional["Result"]] = relationship(
        "Result", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
