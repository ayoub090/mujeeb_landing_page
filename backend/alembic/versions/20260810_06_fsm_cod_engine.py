"""Add persistent COD FSM and order tracking fields."""

from alembic import op
import sqlalchemy as sa

revision = "20260810_06"
down_revision = "20260801_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("orders")}
    additions = {
        "address_data": sa.Column("address_data", sa.JSON(), nullable=False, server_default="{}"),
        "llm_decision": sa.Column("llm_decision", sa.JSON(), nullable=False, server_default="{}"),
        "upsell_status": sa.Column("upsell_status", sa.String(32), nullable=False, server_default="not_offered"),
        "tracking_number": sa.Column("tracking_number", sa.String(120), nullable=True),
        "carrier_name": sa.Column("carrier_name", sa.String(80), nullable=True),
        "billing_status": sa.Column("billing_status", sa.String(32), nullable=False, server_default="UNBILLED"),
    }
    for name, column in additions.items():
        if name not in columns:
            op.add_column("orders", column)
    if "fsm_conversations" not in inspector.get_table_names():
        op.create_table(
            "fsm_conversations",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("phone_number", sa.String(32), nullable=False),
            sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("current_state", sa.String(64), nullable=False, server_default="AWAITING_CONFIRMATION"),
            sa.Column("session_data", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("phone_number", "order_id", name="uq_fsm_phone_order"),
        )
        op.create_index("ix_fsm_conversations_phone_number", "fsm_conversations", ["phone_number"])
        op.create_index("ix_fsm_conversations_order_id", "fsm_conversations", ["order_id"])


def downgrade() -> None:
    op.drop_table("fsm_conversations")
    for name in ("billing_status", "carrier_name", "tracking_number", "upsell_status", "llm_decision", "address_data"):
        op.drop_column("orders", name)
