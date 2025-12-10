from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as PgEnum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TopicCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "topic_campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query: Mapped[str] = mapped_column(String(512), nullable=False)
    seed_urls: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    allowed_domains: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    pages_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    follow_links: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[CampaignStatus] = mapped_column(
        PgEnum(
            CampaignStatus,
            name="campaign_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=CampaignStatus.ACTIVE,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    pages: Mapped[list["CrawledPage"]] = relationship(
        "CrawledPage", back_populates="campaign", cascade="all, delete-orphan"
    )


__all__ = ["TopicCampaign", "CampaignStatus"]
