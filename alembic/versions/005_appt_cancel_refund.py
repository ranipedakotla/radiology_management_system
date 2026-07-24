from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_appt_cancel_refund"
down_revision = "0004_appt_form_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("cancelled_at", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("cancel_reason", sa.Text(), nullable=True))
    op.add_column("appointments", sa.Column("refund_amount", sa.Integer(), nullable=True))
    op.add_column("appointments", sa.Column("refund_mode", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "refund_mode")
    op.drop_column("appointments", "refund_amount")
    op.drop_column("appointments", "cancel_reason")
    op.drop_column("appointments", "cancelled_at")
