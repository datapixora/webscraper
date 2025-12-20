"""add optional project_id to products

Revision ID: 0014
Revises: 0013
Create Date: 2025-12-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("project_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_products_project_id"), "products", ["project_id"], unique=False)
    op.create_foreign_key(
        "products_project_id_fkey", "products", "projects", ["project_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("products_project_id_fkey", "products", type_="foreignkey")
    op.drop_index(op.f("ix_products_project_id"), table_name="products")
    op.drop_column("products", "project_id")
