# migrations/versions/xxxx_appt_extra_fields.py
from alembic import op
import sqlalchemy as sa

revision = "xxxx_appt_extra_fields"
down_revision = "xxxx_patient_extra_fields"
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("appointments") as batch:
        batch.add_column(sa.Column("patient_name_snapshot", sa.String(length=160), nullable=True))
        batch.add_column(sa.Column("doctor_name_snapshot", sa.String(length=160), nullable=True))
        batch.add_column(sa.Column("department", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("discount_reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("referral_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("referral_amount", sa.Integer(), nullable=True, server_default="0"))
        batch.add_column(sa.Column("med_history_file_path", sa.String(length=300), nullable=True))

def downgrade():
    with op.batch_alter_table("appointments") as batch:
        batch.drop_column("med_history_file_path")
        batch.drop_column("referral_amount")
        batch.drop_column("referral_name")
        batch.drop_column("discount_reason")
        batch.drop_column("department")
        batch.drop_column("doctor_name_snapshot")
        batch.drop_column("patient_name_snapshot")
