"""Add BLOCKED status to job_status enum

Revision ID: 0010
Revises: 0009
Create Date: 2025-01-20

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add BLOCKED value to job_status enum."""
    # PostgreSQL enum alteration
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'blocked'")


def downgrade() -> None:
    """
    Downgrade not supported for PostgreSQL enum types.
    Removing enum values requires recreating the type and updating all dependent columns.
    """
    pass
