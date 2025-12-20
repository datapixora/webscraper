from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import Enum as PgEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TopicStatus(str, Enum):
    PENDING = "pending"
    SEARCHING = "searching"
    COMPLETED = "completed"
    FAILED = "failed"


class Topic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "topics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(String(512), nullable=False)
    search_engine: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    max_results: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    status: Mapped[TopicStatus] = mapped_column(
        PgEnum(TopicStatus, name="topic_status", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
        default=TopicStatus.PENDING,
    )

    urls: Mapped[list["TopicURL"]] = relationship(
        "TopicURL", back_populates="topic", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="topic", cascade="all, delete")
    exports: Mapped[list["Export"]] = relationship(
        "Export", back_populates="topic", cascade="all, delete-orphan"
    )


__all__ = ["Topic", "TopicStatus"]
