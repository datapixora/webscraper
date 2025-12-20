"""add topic_id to jobs

Revision ID: 0008
Revises: 0007
Create Date: 2025-12-11 14:02:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add topic_id column to jobs table
    op.add_column("jobs", sa.Column("topic_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_jobs_topic_id"), "jobs", ["topic_id"], unique=False)
    op.create_foreign_key("fk_jobs_topic_id", "jobs", "topics", ["topic_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_jobs_topic_id", "jobs", type_="foreignkey")
    op.drop_index(op.f("ix_jobs_topic_id"), table_name="jobs")
    op.drop_column("jobs", "topic_id")
