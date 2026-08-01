"""Custom store API keys and order payload fields."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260801_02"
down_revision = "20260730_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "store_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_store_api_keys_store_id", "store_api_keys", ["store_id"])
    op.create_index("ix_store_api_keys_prefix", "store_api_keys", ["prefix"])
    op.create_index("ix_store_api_keys_secret_hash", "store_api_keys", ["secret_hash"], unique=True)
    op.add_column("orders", sa.Column("items", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("orders", sa.Column("shipping_city", sa.String(length=120), nullable=True))
    op.add_column("orders", sa.Column("shipping_address_encrypted", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "shipping_address_encrypted")
    op.drop_column("orders", "shipping_city")
    op.drop_column("orders", "items")
    op.drop_index("ix_store_api_keys_secret_hash", table_name="store_api_keys")
    op.drop_index("ix_store_api_keys_prefix", table_name="store_api_keys")
    op.drop_index("ix_store_api_keys_store_id", table_name="store_api_keys")
    op.drop_table("store_api_keys")
