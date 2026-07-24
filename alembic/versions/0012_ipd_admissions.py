# alembic/versions/0012_ipd_admissions.py
from alembic import op
import sqlalchemy as sa

revision = "0012_ipd_admissions"
down_revision = "0008_ipd_master"
branch_labels = None
depends_on = None

def _has_table(name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return name in insp.get_table_names()

def upgrade():
    if not _has_table("ipd_admissions"):
        op.create_table(
            "ipd_admissions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("admission_no", sa.String(20), nullable=False, unique=True),
            sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("doctor_id", sa.Integer, sa.ForeignKey("doctors.id"), nullable=False),
            sa.Column("bed_id", sa.Integer, sa.ForeignKey("beds.id"), nullable=False),
            sa.Column("admit_datetime", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("reason", sa.Text),
            sa.Column("status", sa.String(20), nullable=False, server_default="admitted"),
            sa.Column("created_by_staff_id", sa.Integer, sa.ForeignKey("staff.id")),
        )

    if not _has_table("ipd_transfers"):
        op.create_table(
            "ipd_transfers",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("admission_id", sa.Integer, sa.ForeignKey("ipd_admissions.id"), nullable=False),
            sa.Column("from_bed_id", sa.Integer, sa.ForeignKey("beds.id")),
            sa.Column("to_bed_id", sa.Integer, sa.ForeignKey("beds.id"), nullable=False),
            sa.Column("transfer_datetime", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("reason", sa.Text),
        )

    if not _has_table("ipd_discharges"):
        op.create_table(
            "ipd_discharges",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("admission_id", sa.Integer, sa.ForeignKey("ipd_admissions.id"), nullable=False, unique=True),
            sa.Column("discharge_datetime", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("outcome", sa.String(30), nullable=False, server_default="recovered"),
            sa.Column("notes", sa.Text),
        )

def downgrade():
    # drop only if present (safe for dev)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "ipd_discharges" in insp.get_table_names():
        op.drop_table("ipd_discharges")
    if "ipd_transfers" in insp.get_table_names():
        op.drop_table("ipd_transfers")
    if "ipd_admissions" in insp.get_table_names():
        op.drop_table("ipd_admissions")
