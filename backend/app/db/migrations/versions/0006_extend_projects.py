"""extend projects with new fields

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-11 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add content classification
    op.add_column("projects", sa.Column("content_type", sa.String(length=50), nullable=False, server_default="custom"))

    # Add URL rules (JSON arrays)
    op.add_column("projects", sa.Column("allowed_domains", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("projects", sa.Column("url_include_patterns", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("projects", sa.Column("url_exclude_patterns", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("projects", sa.Column("max_urls_per_run", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("max_total_urls", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("deduplication_enabled", sa.Boolean(), nullable=False, server_default="true"))

    # Add scraping behavior
    op.add_column("projects", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("projects", sa.Column("request_timeout", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("projects", sa.Column("respect_robots_txt", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("projects", sa.Column("random_delay_min_ms", sa.Integer(), nullable=False, server_default="1000"))
    op.add_column("projects", sa.Column("random_delay_max_ms", sa.Integer(), nullable=False, server_default="3000"))
    op.add_column("projects", sa.Column("max_concurrent_jobs", sa.Integer(), nullable=False, server_default="3"))

    # Add output settings
    op.add_column("projects", sa.Column("output_formats", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='["jsonl"]'))
    op.add_column("projects", sa.Column("output_grouping", sa.String(length=50), nullable=False, server_default="per_topic"))
    op.add_column("projects", sa.Column("max_rows_per_file", sa.Integer(), nullable=True))
    op.add_column("projects", sa.Column("file_naming_template", sa.String(length=255), nullable=True))
    op.add_column("projects", sa.Column("compression_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("projects", sa.Column("auto_export_enabled", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    # Remove output settings
    op.drop_column("projects", "auto_export_enabled")
    op.drop_column("projects", "compression_enabled")
    op.drop_column("projects", "file_naming_template")
    op.drop_column("projects", "max_rows_per_file")
    op.drop_column("projects", "output_grouping")
    op.drop_column("projects", "output_formats")

    # Remove scraping behavior
    op.drop_column("projects", "max_concurrent_jobs")
    op.drop_column("projects", "random_delay_max_ms")
    op.drop_column("projects", "random_delay_min_ms")
    op.drop_column("projects", "respect_robots_txt")
    op.drop_column("projects", "request_timeout")
    op.drop_column("projects", "max_retries")

    # Remove URL rules
    op.drop_column("projects", "deduplication_enabled")
    op.drop_column("projects", "max_total_urls")
    op.drop_column("projects", "max_urls_per_run")
    op.drop_column("projects", "url_exclude_patterns")
    op.drop_column("projects", "url_include_patterns")
    op.drop_column("projects", "allowed_domains")

    # Remove content classification
    op.drop_column("projects", "content_type")
