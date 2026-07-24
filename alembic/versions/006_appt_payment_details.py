from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_appt_payment_details"
down_revision = "0005_appt_cancel_refund"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("amount_payable", sa.Integer(), server_default="0", nullable=False))

    # cash denominations (booking)
    op.add_column("appointments", sa.Column("cash_500", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_200", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_100", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_50", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_20", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_10", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("cash_total", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("utr_no", sa.String(length=64), nullable=True))

    # refund details
    op.add_column("appointments", sa.Column("refund_cash_500", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_200", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_100", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_50", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_20", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_10", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_cash_total", sa.Integer(), server_default="0", nullable=True))
    op.add_column("appointments", sa.Column("refund_utr_no", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "refund_utr_no")
    op.drop_column("appointments", "refund_cash_total")
    op.drop_column("appointments", "refund_cash_10")
    op.drop_column("appointments", "refund_cash_20")
    op.drop_column("appointments", "refund_cash_50")
    op.drop_column("appointments", "refund_cash_100")
    op.drop_column("appointments", "refund_cash_200")
    op.drop_column("appointments", "refund_cash_500")
    op.drop_column("appointments", "utr_no")
    op.drop_column("appointments", "cash_total")
    op.drop_column("appointments", "cash_10")
    op.drop_column("appointments", "cash_20")
    op.drop_column("appointments", "cash_50")
    op.drop_column("appointments", "cash_100")
    op.drop_column("appointments", "cash_200")
    op.drop_column("appointments", "cash_500")
    op.drop_column("appointments", "amount_payable")
