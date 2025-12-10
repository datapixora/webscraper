from __future__ import annotations

from enum import Enum
from typing import Optional

from sqlalchemy import Enum as PgEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PageStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class CrawledPage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "crawled_pages"

    campaign_id: Mapped[str] = mapped_column(ForeignKey("topic_campaigns.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(512))
    raw_html: Mapped[Optional[str]] = mapped_column(Text)
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[PageStatus] = mapped_column(
        PgEnum(PageStatus, name="page_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        default=PageStatus.SUCCESS,
    )
    campaign: Mapped["TopicCampaign"] = relationship("TopicCampaign", back_populates="pages")


__all__ = ["CrawledPage", "PageStatus"]
