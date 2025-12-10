"""add topics and topic_urls

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-10 18:40:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    topic_status = postgresql.ENUM(
        "pending", "searching", "completed", "failed", name="topic_status", create_type=False
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'topic_status') THEN
                CREATE TYPE topic_status AS ENUM ('pending','searching','completed','failed');
            END IF;
        END$$;
        """
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("search_engine", sa.String(length=50), nullable=False),
        sa.Column("max_results", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("status", topic_status, nullable=False, server_default="pending"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "topic_urls",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("topic_id", sa.String(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("selected_for_scraping", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("scraped", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topic_urls_topic_id"), "topic_urls", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_topic_urls_topic_id"), table_name="topic_urls")
    op.drop_table("topic_urls")
    op.drop_table("topics")
    op.execute("DROP TYPE IF EXISTS topic_status")
