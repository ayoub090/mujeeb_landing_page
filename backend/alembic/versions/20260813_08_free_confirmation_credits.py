"""Track the 50 free confirmations independently from order intake."""

from alembic import op
import sqlalchemy as sa


revision = "20260813_08"
down_revision = "20260812_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column(
            "free_confirmations_remaining",
            sa.Integer(),
            nullable=False,
            server_default="50",
        ),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "free_confirmations_remaining")
