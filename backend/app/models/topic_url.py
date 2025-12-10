from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TopicURL(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "topic_urls"

    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512))
    snippet: Mapped[Optional[str]] = mapped_column(Text)
    rank: Mapped[Optional[int]] = mapped_column(Integer)
    selected_for_scraping: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scraped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="urls")


__all__ = ["TopicURL"]
