"""First-party lead capture and funnel analytics."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260801_03"
down_revision = "20260801_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name_encrypted", sa.Text(), nullable=False),
        sa.Column("company", sa.String(length=180), nullable=False),
        sa.Column("whatsapp_encrypted", sa.Text(), nullable=False),
        sa.Column("whatsapp_hash", sa.String(length=64), nullable=False),
        sa.Column("email_encrypted", sa.Text(), nullable=False),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("monthly_orders", sa.String(length=32), nullable=False),
        sa.Column("attribution", sa.JSON(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("landing_page", sa.Text(), nullable=True),
        sa.Column("consent_text_version", sa.String(length=32), nullable=False),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_business_leads_whatsapp_hash", ["whatsapp_hash"]),
        ("ix_business_leads_email_hash", ["email_hash"]),
        ("ix_business_leads_status", ["status"]),
        ("ix_business_leads_created_at", ["created_at"]),
    ):
        op.create_index(name, "business_leads", columns)

    op.create_table(
        "funnel_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_name", sa.String(length=48), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("attribution", sa.JSON(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_funnel_events_event_name", ["event_name"]),
        ("ix_funnel_events_session_id", ["session_id"]),
        ("ix_funnel_events_created_at", ["created_at"]),
    ):
        op.create_index(name, "funnel_events", columns)


def downgrade() -> None:
    op.drop_table("funnel_events")
    op.drop_table("business_leads")
