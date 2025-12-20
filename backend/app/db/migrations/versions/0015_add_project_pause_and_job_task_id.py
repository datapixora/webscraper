"""add project pause flags and celery task id

Revision ID: 0015
Revises: 0014
Create Date: 2025-12-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("is_paused", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("projects", sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("projects", "is_paused", server_default=None)

    op.add_column("jobs", sa.Column("celery_task_id", sa.String(length=128), nullable=True))

    # extend job_status enum with queued and cancelled
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'queued'")
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    op.drop_column("jobs", "celery_task_id")
    op.drop_column("projects", "paused_at")
    op.drop_column("projects", "is_paused")
