"""Activation analytics, durable email jobs, and automated deletion requests."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260801_05"
down_revision: str | None = "20260801_04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("business_leads", sa.Column("session_id", sa.String(length=64), nullable=True))
    op.create_index("ix_business_leads_session_id", "business_leads", ["session_id"])

    op.add_column("funnel_events", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("funnel_events", sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "funnel_events", sa.Column("source", sa.String(length=32), nullable=False, server_default="client")
    )
    op.add_column(
        "funnel_events",
        sa.Column("properties", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.create_foreign_key(
        "fk_funnel_events_user_id", "funnel_events", "users", ["user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key(
        "fk_funnel_events_store_id", "funnel_events", "stores", ["store_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_funnel_events_user_id", "funnel_events", ["user_id"])
    op.create_index("ix_funnel_events_store_id", "funnel_events", ["store_id"])
    op.create_index("ix_funnel_events_source", "funnel_events", ["source"])

    op.create_table(
        "email_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dedupe_key", sa.String(length=180), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("recipient_encrypted", sa.Text(), nullable=False),
        sa.Column("recipient_hash", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, columns, unique in (
        ("ix_email_jobs_dedupe_key", ["dedupe_key"], True),
        ("ix_email_jobs_kind", ["kind"], False),
        ("ix_email_jobs_recipient_hash", ["recipient_hash"], False),
        ("ix_email_jobs_status", ["status"], False),
        ("ix_email_jobs_next_attempt_at", ["next_attempt_at"], False),
    ):
        op.create_index(name, "email_jobs", columns, unique=unique)

    op.create_table(
        "data_deletion_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    for name, columns in (
        ("ix_data_deletion_requests_user_id", ["user_id"]),
        ("ix_data_deletion_requests_email_hash", ["email_hash"]),
        ("ix_data_deletion_requests_status", ["status"]),
        ("ix_data_deletion_requests_scheduled_for", ["scheduled_for"]),
    ):
        op.create_index(name, "data_deletion_requests", columns)


def downgrade() -> None:
    op.drop_table("data_deletion_requests")
    op.drop_table("email_jobs")
    op.drop_index("ix_funnel_events_source", table_name="funnel_events")
    op.drop_index("ix_funnel_events_store_id", table_name="funnel_events")
    op.drop_index("ix_funnel_events_user_id", table_name="funnel_events")
    op.drop_constraint("fk_funnel_events_store_id", "funnel_events", type_="foreignkey")
    op.drop_constraint("fk_funnel_events_user_id", "funnel_events", type_="foreignkey")
    op.drop_column("funnel_events", "properties")
    op.drop_column("funnel_events", "source")
    op.drop_column("funnel_events", "store_id")
    op.drop_column("funnel_events", "user_id")
    op.drop_index("ix_business_leads_session_id", table_name="business_leads")
    op.drop_column("business_leads", "session_id")
