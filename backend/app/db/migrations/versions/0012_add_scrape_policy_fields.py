"""add scrape policy fields

Revision ID: 0012
Revises: 0011
Create Date: 2025-12-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ensure UUID generation available
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.add_column("domain_policies", sa.Column("method", sa.String(length=20), nullable=False, server_default="auto"))
    op.add_column("domain_policies", sa.Column("use_proxy", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("domain_policies", sa.Column("request_delay_ms", sa.Integer(), nullable=False, server_default="1000"))
    op.add_column("domain_policies", sa.Column("max_concurrency", sa.Integer(), nullable=False, server_default="2"))
    op.add_column("domain_policies", sa.Column("user_agent", sa.String(length=512), nullable=True))
    op.add_column("domain_policies", sa.Column("block_resources", sa.Boolean(), nullable=False, server_default=sa.true()))

    # Seed a helpful default policy for a known Cloudflare-protected domain
    op.execute(
        """
        INSERT INTO domain_policies (id, domain, enabled, method, use_proxy, request_delay_ms, max_concurrency, user_agent, block_resources, created_at, updated_at)
        SELECT uuid_generate_v4(), 'motor3dmodel.ir', true, 'playwright', true, 1500, 1, NULL, true, now(), now()
        WHERE NOT EXISTS (SELECT 1 FROM domain_policies WHERE domain = 'motor3dmodel.ir');
        """
    )

    # Clean server defaults for future inserts
    op.alter_column("domain_policies", "method", server_default=None)
    op.alter_column("domain_policies", "use_proxy", server_default=None)
    op.alter_column("domain_policies", "request_delay_ms", server_default=None)
    op.alter_column("domain_policies", "max_concurrency", server_default=None)
    op.alter_column("domain_policies", "block_resources", server_default=None)


def downgrade() -> None:
    op.drop_column("domain_policies", "block_resources")
    op.drop_column("domain_policies", "user_agent")
    op.drop_column("domain_policies", "max_concurrency")
    op.drop_column("domain_policies", "request_delay_ms")
    op.drop_column("domain_policies", "use_proxy")
    op.drop_column("domain_policies", "method")
