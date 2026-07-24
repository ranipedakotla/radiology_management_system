from alembic import op
import sqlalchemy as sa

revision = '0003_appointments'
down_revision = '0002_people_schedule'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('appointments',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('appointment_no', sa.String(20), unique=True, nullable=False),
        sa.Column('patient_id', sa.Integer, sa.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False),
        sa.Column('doctor_id', sa.Integer, sa.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scheduled_for', sa.DateTime, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='booked'),
        sa.Column('notes', sa.Text, nullable=True),
    )
    op.create_index('ix_appt_doc_time', 'appointments', ['doctor_id','scheduled_for'])

def downgrade():
    op.drop_index('ix_appt_doc_time', table_name='appointments')
    op.drop_table('appointments')