"""billing core: invoices, invoice_items, receipts"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0010_billing"
down_revision = "0009_opd_visit_labtests"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_no", sa.String(20), unique=True, index=True, nullable=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=False, index=True),
        sa.Column("visit_id", sa.Integer, sa.ForeignKey("opd_visits.id"), nullable=True, index=True),
        sa.Column("appointment_id", sa.Integer, sa.ForeignKey("appointments.id"), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("sub_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("tax_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("grand_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("item_type", sa.String(30), nullable=False),  # consultation/lab/radiology/meds/other
        sa.Column("ref_id", sa.Integer, nullable=True),  # e.g., lab_test_id
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("qty", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("line_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
    )

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amount_received", sa.Numeric(12, 2), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),  # Cash/UPI/Card/Other
        sa.Column("utr_no", sa.String(60), nullable=True),

        # cash denominations
        sa.Column("cash_500", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_200", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_100", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_50", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_20", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_10", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("cash_total", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),

        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("receipts")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
