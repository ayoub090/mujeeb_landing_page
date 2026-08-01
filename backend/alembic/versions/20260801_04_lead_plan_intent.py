"""Capture commercial plan intent on marketing leads."""

import sqlalchemy as sa

from alembic import op

revision = "20260801_04"
down_revision = "20260801_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "business_leads",
        sa.Column("selected_plan", sa.String(length=32), nullable=False, server_default="pilot"),
    )
    op.create_index("ix_business_leads_selected_plan", "business_leads", ["selected_plan"])


def downgrade() -> None:
    op.drop_index("ix_business_leads_selected_plan", table_name="business_leads")
    op.drop_column("business_leads", "selected_plan")
