"""add products table

Revision ID: 0013
Revises: 0012
Create Date: 2025-12-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("price_text", sa.String(length=128), nullable=True),
        sa.Column("images_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("categories_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_products_domain"), "products", ["domain"], unique=False)
    op.create_index(op.f("ix_products_url"), "products", ["url"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_url"), table_name="products")
    op.drop_index(op.f("ix_products_domain"), table_name="products")
    op.drop_table("products")
