# alembic revision -m "multi-branch associations"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

revision = "0019_multibranch_associations"
down_revision = "0018_add_permissions_label"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "patient_branch_codes",
        sa.Column("patient_id", sa.Integer, nullable=False),
        sa.Column("branch_id", sa.Integer, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("patient_id", "branch_id"),
        sa.UniqueConstraint("branch_id", "code", name="uq_patient_code_per_branch"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )

    op.create_table(
        "staff_branches",
        sa.Column("staff_id", sa.Integer, nullable=False),
        sa.Column("branch_id", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("staff_id", "branch_id"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )

    op.create_table(
        "doctor_branches",
        sa.Column("doctor_id", sa.Integer, nullable=False),
        sa.Column("branch_id", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("doctor_id", "branch_id"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )

    # -------- optional backfill from old columns if they exist --------
    conn = op.get_bind()

    # If patients had (branch_id, patient_code), seed patient_branch_codes
    try:
        conn.exec_driver_sql("""
            INSERT IGNORE INTO patient_branch_codes (patient_id, branch_id, code)
            SELECT id, branch_id, patient_code
            FROM patients
            WHERE branch_id IS NOT NULL AND patient_code IS NOT NULL
        """)
    except Exception:
        pass

    # If staff had a branch_id, seed staff_branches
    try:
        conn.exec_driver_sql("""
            INSERT IGNORE INTO staff_branches (staff_id, branch_id)
            SELECT id, branch_id FROM staff WHERE branch_id IS NOT NULL
        """)
    except Exception:
        pass

    # If doctors had a branch_id, seed doctor_branches
    try:
        conn.exec_driver_sql("""
            INSERT IGNORE INTO doctor_branches (doctor_id, branch_id)
            SELECT id, branch_id FROM doctors WHERE branch_id IS NOT NULL
        """)
    except Exception:
        pass


def downgrade():
    op.drop_table("doctor_branches")
    op.drop_table("staff_branches")
    op.drop_table("patient_branch_codes")
