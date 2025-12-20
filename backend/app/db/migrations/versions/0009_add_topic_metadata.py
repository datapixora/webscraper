"""add category and directory_path to topics

Revision ID: 0009
Revises: 0008
Create Date: 2025-12-11 15:40:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("category", sa.String(length=255), nullable=True))
    op.add_column("topics", sa.Column("directory_path", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("topics", "directory_path")
    op.drop_column("topics", "category")

