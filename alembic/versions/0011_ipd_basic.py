from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0011_ipd_basic"
down_revision = "0010_invoice_pdf_cols"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ipd_admissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("admission_no", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("doctor_id", sa.Integer, sa.ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False, index=True),

        sa.Column("admit_datetime", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("reason", sa.Text, nullable=True),

        sa.Column("current_ward", sa.String(60), nullable=True),
        sa.Column("current_room", sa.String(30), nullable=True),
        sa.Column("current_bed", sa.String(30), nullable=True),

        sa.Column("status", sa.String(20), nullable=False, server_default="admitted"),  # admitted | discharged

        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ipd_transfers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("admission_id", sa.Integer, sa.ForeignKey("ipd_admissions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("from_ward", sa.String(60), nullable=True),
        sa.Column("from_room", sa.String(30), nullable=True),
        sa.Column("from_bed", sa.String(30), nullable=True),
        sa.Column("to_ward", sa.String(60), nullable=True),
        sa.Column("to_room", sa.String(30), nullable=True),
        sa.Column("to_bed", sa.String(30), nullable=True),
        sa.Column("transfer_datetime", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
    )

    op.create_table(
        "ipd_discharges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("admission_id", sa.Integer, sa.ForeignKey("ipd_admissions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("discharge_datetime", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("outcome", sa.String(20), nullable=True),  # Stable | Recovered | Referred | Deceased | Other
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("advice", sa.Text, nullable=True),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
    )

def downgrade():
    op.drop_table("ipd_discharges")
    op.drop_table("ipd_transfers")
    op.drop_table("ipd_admissions")
