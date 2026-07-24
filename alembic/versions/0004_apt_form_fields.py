from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_appt_form_fields"
down_revision = "0003_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("shift", sa.String(20), nullable=True))
    op.add_column("appointments", sa.Column("slot_label", sa.String(20), nullable=True))
    op.add_column("appointments", sa.Column("priority", sa.String(20), server_default="Normal", nullable=False))
    op.add_column("appointments", sa.Column("payment_mode", sa.String(20), server_default="Cash", nullable=False))
    op.add_column("appointments", sa.Column("doctor_fee", sa.Integer(), nullable=True))
    op.add_column("appointments", sa.Column("discount_pct", sa.Integer(), server_default="0", nullable=False))
    op.add_column("appointments", sa.Column("is_video", sa.Boolean(), server_default=sa.text("0"), nullable=False))


def downgrade() -> None:
    op.drop_column("appointments", "is_video")
    op.drop_column("appointments", "discount_pct")
    op.drop_column("appointments", "doctor_fee")
    op.drop_column("appointments", "payment_mode")
    op.drop_column("appointments", "priority")
    op.drop_column("appointments", "slot_label")
    op.drop_column("appointments", "shift")
