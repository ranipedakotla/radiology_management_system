from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_entity_codes"
down_revision = "0007_opd_visits"   # adjust if your last revision id differs
branch_labels = None
depends_on = None


def upgrade() -> None:
    # table that stores rolling monthly counters per prefix (e.g., PAT/DOC/STF)
    op.create_table(
        "id_sequences",
        sa.Column("name", sa.String(length=10), nullable=False),     # e.g., PAT / DOC / STF
        sa.Column("yyyymm", sa.String(length=6), nullable=False),    # e.g., 202508
        sa.Column("counter", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("name", "yyyymm"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # add human-readable codes to entities
    op.add_column("patients", sa.Column("patient_code", sa.String(length=20), nullable=True))
    op.create_unique_constraint("uq_patients_patient_code", "patients", ["patient_code"])

    op.add_column("staff", sa.Column("staff_code", sa.String(length=20), nullable=True))
    op.create_unique_constraint("uq_staff_staff_code", "staff", ["staff_code"])

    op.add_column("doctors", sa.Column("doctor_code", sa.String(length=20), nullable=True))
    op.create_unique_constraint("uq_doctors_doctor_code", "doctors", ["doctor_code"])


def downgrade() -> None:
    op.drop_constraint("uq_doctors_doctor_code", "doctors", type_="unique")
    op.drop_column("doctors", "doctor_code")

    op.drop_constraint("uq_staff_staff_code", "staff", type_="unique")
    op.drop_column("staff", "staff_code")

    op.drop_constraint("uq_patients_patient_code", "patients", type_="unique")
    op.drop_column("patients", "patient_code")

    op.drop_table("id_sequences")
