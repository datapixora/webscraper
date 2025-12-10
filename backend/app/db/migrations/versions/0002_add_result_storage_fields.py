"""add storage fields to results

Revision ID: 0002
Revises: 0001
Create Date: 2025-12-10 12:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("results", sa.Column("raw_html_path", sa.String(length=512), nullable=True))
    op.add_column("results", sa.Column("raw_html_checksum", sa.String(length=128), nullable=True))
    op.add_column("results", sa.Column("raw_html_size", sa.Integer(), nullable=True))
    op.add_column("results", sa.Column("raw_html_compressed_size", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("results", "raw_html_compressed_size")
    op.drop_column("results", "raw_html_size")
    op.drop_column("results", "raw_html_checksum")
    op.drop_column("results", "raw_html_path")
