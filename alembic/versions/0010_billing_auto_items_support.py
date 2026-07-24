from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0010_billing_auto_items_support"
down_revision = "0010_billing"  # <-- change to your last revision id
branch_labels = None
depends_on = None


def upgrade():
    # --- invoices ---
    if not op.get_bind().dialect.has_table(op.get_bind(), "invoices"):
        op.create_table(
            "invoices",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=False, index=True),
            sa.Column("visit_id", sa.Integer, sa.ForeignKey("opd_visits.id"), nullable=True, index=True),
            sa.Column("appointment_id", sa.Integer, sa.ForeignKey("appointments.id"), nullable=True, index=True),
            sa.Column("invoice_no", sa.String(20), unique=True, index=True),
            sa.Column("status", sa.String(20), server_default=sa.text("'draft'")),
            sa.Column("sub_total", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("discount_pct", sa.Numeric(5, 2), nullable=True),
            sa.Column("discount_amount", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("tax_pct", sa.Numeric(5, 2), nullable=True),
            sa.Column("tax_amount", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("grand_total", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("amount_paid", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    else:
        with op.batch_alter_table("invoices") as batch:
            if not _has_col("invoices", "visit_id"):
                batch.add_column(sa.Column("visit_id", sa.Integer, nullable=True))
                batch.create_foreign_key(None, "opd_visits", ["visit_id"], ["id"])
                batch.create_index("ix_invoices_visit_id", ["visit_id"])
            if not _has_col("invoices", "appointment_id"):
                batch.add_column(sa.Column("appointment_id", sa.Integer, nullable=True))
                batch.create_foreign_key(None, "appointments", ["appointment_id"], ["id"])
                batch.create_index("ix_invoices_appointment_id", ["appointment_id"])

    # --- invoice_items ---
    if not op.get_bind().dialect.has_table(op.get_bind(), "invoice_items"):
        op.create_table(
            "invoice_items",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id", ondelete="CASCADE"), index=True),
            sa.Column("item_type", sa.String(30), nullable=False),
            sa.Column("ref_id", sa.Integer, nullable=True),
            sa.Column("description", sa.String(255), nullable=False),
            sa.Column("qty", sa.Integer, server_default="1"),
            sa.Column("unit_price", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("line_total", sa.Numeric(12, 2), server_default=sa.text("0.00")),
        )
    else:
        with op.batch_alter_table("invoice_items") as batch:
            for name, col in [
                ("item_type", sa.String(30)),
                ("ref_id", sa.Integer()),
                ("description", sa.String(255)),
                ("qty", sa.Integer()),
                ("unit_price", sa.Numeric(12, 2)),
                ("line_total", sa.Numeric(12, 2)),
            ]:
                if not _has_col("invoice_items", name):
                    # sensible defaults
                    if name == "qty":
                        batch.add_column(sa.Column(name, col, server_default="1"))
                    elif name in ("unit_price", "line_total"):
                        batch.add_column(sa.Column(name, col, server_default=sa.text("0.00")))
                    else:
                        batch.add_column(sa.Column(name, col, nullable=(name != "item_type")))

    # --- receipts ---
    if not op.get_bind().dialect.has_table(op.get_bind(), "receipts"):
        op.create_table(
            "receipts",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("invoice_id", sa.Integer, sa.ForeignKey("invoices.id", ondelete="CASCADE"), index=True),
            sa.Column("amount_received", sa.Numeric(12, 2), nullable=False),
            sa.Column("mode", sa.String(20), nullable=False),  # Cash | UPI | Card
            sa.Column("utr_no", sa.String(80), nullable=True),
            sa.Column("cash_500", sa.Integer, server_default="0"),
            sa.Column("cash_200", sa.Integer, server_default="0"),
            sa.Column("cash_100", sa.Integer, server_default="0"),
            sa.Column("cash_50", sa.Integer, server_default="0"),
            sa.Column("cash_20", sa.Integer, server_default="0"),
            sa.Column("cash_10", sa.Integer, server_default="0"),
            sa.Column("cash_total", sa.Numeric(12, 2), server_default=sa.text("0.00")),
            sa.Column("received_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
    else:
        with op.batch_alter_table("receipts") as batch:
            for name, col in [
                ("mode", sa.String(20)),
                ("utr_no", sa.String(80)),
                ("cash_500", sa.Integer()),
                ("cash_200", sa.Integer()),
                ("cash_100", sa.Integer()),
                ("cash_50", sa.Integer()),
                ("cash_20", sa.Integer()),
                ("cash_10", sa.Integer()),
                ("cash_total", sa.Numeric(12, 2)),
                ("received_at", sa.DateTime()),
            ]:
                if not _has_col("receipts", name):
                    if name in ("cash_500","cash_200","cash_100","cash_50","cash_20","cash_10"):
                        batch.add_column(sa.Column(name, col, server_default="0"))
                    elif name == "cash_total":
                        batch.add_column(sa.Column(name, col, server_default=sa.text("0.00")))
                    elif name == "mode":
                        batch.add_column(sa.Column(name, col, nullable=False))
                    else:
                        batch.add_column(sa.Column(name, col))


def downgrade():
    # safe, non-destructive downgrade (no drops)
    pass


def _has_col(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols
