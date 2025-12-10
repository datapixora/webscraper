from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Result(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "results"

    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    structured_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)  # preview/snippet
    raw_html_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_html_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_html_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_html_compressed_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    job: Mapped["Job"] = relationship("Job", back_populates="result")
