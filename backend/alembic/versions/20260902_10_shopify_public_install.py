"""Add secure pending installs for the public Shopify App Store flow."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260902_10"
down_revision = "20260820_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("oauth_states", "store_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.add_column("oauth_states", sa.Column("external_reference", sa.String(length=180), nullable=True))
    op.create_index("ix_oauth_states_external_reference", "oauth_states", ["external_reference"])
    op.create_table(
        "shopify_pending_installs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shop", sa.String(length=180), nullable=False),
        sa.Column("shop_name", sa.String(length=160), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("claim_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_token_hash"),
        sa.UniqueConstraint("shop"),
    )
    op.create_index("ix_shopify_pending_installs_shop", "shopify_pending_installs", ["shop"])
    op.create_index("ix_shopify_pending_installs_claim_token_hash", "shopify_pending_installs", ["claim_token_hash"])
    op.create_index("ix_shopify_pending_installs_expires_at", "shopify_pending_installs", ["expires_at"])


def downgrade() -> None:
    op.drop_table("shopify_pending_installs")
    op.drop_index("ix_oauth_states_external_reference", table_name="oauth_states")
    op.drop_column("oauth_states", "external_reference")
    op.alter_column("oauth_states", "store_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
