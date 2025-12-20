from sqlalchemy import JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"

    project_id: Mapped[str | None] = mapped_column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    price_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    images_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    categories_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tags_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
