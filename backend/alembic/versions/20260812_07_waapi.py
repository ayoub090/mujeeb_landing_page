"""Add optional WAAPI connections."""
from alembic import op
import sqlalchemy as sa

revision = "20260812_07"
down_revision = "20260810_06"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "waapi_connections",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("store_id", sa.Uuid(), sa.ForeignKey("stores.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instance_id", sa.String(64), nullable=False),
        sa.Column("api_token_encrypted", sa.Text(), nullable=False),
        sa.Column("webhook_token_encrypted", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="configured"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", name="uq_waapi_store"),
    )

def downgrade() -> None:
    op.drop_table("waapi_connections")
