from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_opd_visits"
down_revision = "0006_appt_payment_details"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opd_visits",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("visit_id", sa.String(20), unique=True, index=True, nullable=False),
        sa.Column("patient_id", sa.Integer, sa.ForeignKey("patients.id", ondelete="RESTRICT"), index=True, nullable=False),
        sa.Column("doctor_id", sa.Integer, sa.ForeignKey("doctors.id", ondelete="RESTRICT"), index=True, nullable=False),
        sa.Column("appointment_id", sa.Integer, sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("visit_date", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),

        # clinical notes
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),

        # vitals
        sa.Column("height_cm", sa.Integer(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("temp_c", sa.Float(), nullable=True),
        sa.Column("bp_systolic", sa.Integer(), nullable=True),
        sa.Column("bp_diastolic", sa.Integer(), nullable=True),
        sa.Column("pulse", sa.Integer(), nullable=True),
        sa.Column("resp_rate", sa.Integer(), nullable=True),
        sa.Column("spo2", sa.Integer(), nullable=True),
    )

    op.create_table(
        "opd_visit_diagnoses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("visit_id", sa.Integer, sa.ForeignKey("opd_visits.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("icd_code", sa.String(20), nullable=True),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("visit_id", sa.Integer, sa.ForeignKey("opd_visits.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("prescribed_by_staff_id", sa.Integer, sa.ForeignKey("staff.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "prescription_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("prescription_id", sa.Integer, sa.ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("drug_name", sa.String(120), nullable=False),
        sa.Column("dose", sa.String(60), nullable=True),        # e.g. 500 mg
        sa.Column("frequency", sa.String(60), nullable=True),   # e.g. 1-0-1
        sa.Column("duration", sa.String(60), nullable=True),    # e.g. 5 days
        sa.Column("route", sa.String(40), nullable=True),       # e.g. PO
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("prescription_items")
    op.drop_table("prescriptions")
    op.drop_table("opd_visit_diagnoses")
    op.drop_table("opd_visits")
