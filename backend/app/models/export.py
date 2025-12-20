from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExportStatus(str, Enum):
    """Status of an export file generation."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class Export(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Export model for storing generated result files."""

    __tablename__ = "exports"

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Export metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # jsonl, csv, zip
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ExportStatus.PENDING, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="exports")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="exports")
