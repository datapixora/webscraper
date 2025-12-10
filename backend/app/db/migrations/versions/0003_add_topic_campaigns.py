"""add topic campaigns and crawled pages

Revision ID: 0003
Revises: 0002
Create Date: 2025-12-10 13:35:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    campaign_status = postgresql.ENUM(
        "active", "paused", "completed", "failed", name="campaign_status", create_type=False
    )
    page_status = postgresql.ENUM("success", "failed", "skipped", name="page_status", create_type=False)

    # Create enums if not exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'campaign_status') THEN
                CREATE TYPE campaign_status AS ENUM ('active', 'paused', 'completed', 'failed');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'page_status') THEN
                CREATE TYPE page_status AS ENUM ('success', 'failed', 'skipped');
            END IF;
        END$$;
        """
    )

    op.create_table(
        "topic_campaigns",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("seed_urls", sa.JSON(), nullable=False),
        sa.Column("allowed_domains", sa.JSON(), nullable=True),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("pages_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("follow_links", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", campaign_status, nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_topic_campaigns_name"), "topic_campaigns", ["name"], unique=False)

    op.create_table(
        "crawled_pages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("campaign_id", sa.String(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("status", page_status, nullable=False, server_default="success"),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["topic_campaigns.id"],
            name=op.f("fk_crawled_pages_campaign_id_topic_campaigns"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_crawled_pages_campaign_id"), "crawled_pages", ["campaign_id"], unique=False)
    op.create_unique_constraint(op.f("uq_crawled_pages_campaign_url"), "crawled_pages", ["campaign_id", "url"])


def downgrade() -> None:
    op.drop_constraint(op.f("uq_crawled_pages_campaign_url"), "crawled_pages", type_="unique")
    op.drop_index(op.f("ix_crawled_pages_campaign_id"), table_name="crawled_pages")
    op.drop_table("crawled_pages")
    op.drop_index(op.f("ix_topic_campaigns_name"), table_name="topic_campaigns")
    op.drop_table("topic_campaigns")
    op.execute("DROP TYPE IF EXISTS page_status")
    op.execute("DROP TYPE IF EXISTS campaign_status")
