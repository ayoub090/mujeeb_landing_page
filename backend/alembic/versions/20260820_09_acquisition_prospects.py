"""Add the owner-operated acquisition prospect inbox."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260820_09"
down_revision = "20260813_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "acquisition_prospects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company", sa.String(length=180), nullable=False),
        sa.Column("canonical_website", sa.String(length=500), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=True),
        sa.Column("public_email", sa.String(length=320), nullable=True),
        sa.Column("public_phone", sa.String(length=40), nullable=True),
        sa.Column("social_profiles", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("outreach_channel", sa.String(length=32), nullable=True),
        sa.Column("message_draft", sa.Text(), nullable=True),
        sa.Column("last_contacted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_attempts", sa.Integer(), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_website", name="uq_acquisition_prospect_website"),
    )
    op.create_index("ix_acquisition_prospects_country_code", "acquisition_prospects", ["country_code"])
    op.create_index("ix_acquisition_prospects_platform", "acquisition_prospects", ["platform"])
    op.create_index("ix_acquisition_prospects_score", "acquisition_prospects", ["score"])
    op.create_index("ix_acquisition_prospects_status", "acquisition_prospects", ["status"])
    op.create_index(
        "ix_acquisition_prospects_score_status",
        "acquisition_prospects",
        ["score", "status"],
    )


def downgrade() -> None:
    op.drop_table("acquisition_prospects")
