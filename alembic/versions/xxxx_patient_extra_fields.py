# migrations/versions/xxxx_patient_extra_fields.py
from alembic import op
import sqlalchemy as sa

revision = "xxxx_patient_extra_fields"
down_revision = "0019_multibranch_associations"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("patients") as batch:
        batch.add_column(sa.Column("age", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("blood_group", sa.String(length=3), nullable=True))
        batch.add_column(sa.Column("marital_status", sa.String(length=12), nullable=True))
        batch.add_column(sa.Column("email", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("location", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("aadhaar_no", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("aadhaar_file_path", sa.String(length=300), nullable=True))
        batch.create_index("ix_patients_aadhaar_no", ["aadhaar_no"], unique=False)
        batch.create_unique_constraint(
            "uq_patients_hosp_aadhaar",
            ["hospital_id", "aadhaar_no"]
        )

def downgrade():
    with op.batch_alter_table("patients") as batch:
        batch.drop_constraint("uq_patients_hosp_aadhaar", type_="unique")
        batch.drop_index("ix_patients_aadhaar_no")
        batch.drop_column("aadhaar_file_path")
        batch.drop_column("aadhaar_no")
        batch.drop_column("reason")
        batch.drop_column("location")
        batch.drop_column("email")
        batch.drop_column("marital_status")
        batch.drop_column("blood_group")
        batch.drop_column("age")

