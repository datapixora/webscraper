from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DomainPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "domain_policies"

    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="auto")
    use_proxy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    request_delay_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_concurrency: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    block_resources: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
