from alembic import op
import sqlalchemy as sa

revision = '0002_people_schedule'
down_revision = '0001_auth_org'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('staff',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True),
        sa.Column('first_name', sa.String(60), nullable=False),
        sa.Column('last_name', sa.String(60), nullable=False),
        sa.Column('designation', sa.String(60)),
    )
    op.create_table('patients',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('patient_uid', sa.String(20), unique=True, nullable=False),
        sa.Column('first_name', sa.String(60), nullable=False),
        sa.Column('last_name', sa.String(60), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('dob', sa.Date, nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
    )
    op.create_index('ix_patients_uid', 'patients', ['patient_uid'])

    op.create_table('doctors',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('staff_id', sa.Integer, sa.ForeignKey('staff.id', ondelete='CASCADE'), unique=True),
        sa.Column('specialty', sa.String(60), nullable=False),
        sa.Column('consultation_fee', sa.Integer, nullable=True),
    )

    op.create_table('doctor_schedules',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('doctor_id', sa.Integer, sa.ForeignKey('doctors.id', ondelete='CASCADE')),
        sa.Column('schedule_date', sa.Integer, nullable=False),
        sa.Column('start_time', sa.Time, nullable=False),
        sa.Column('end_time', sa.Time, nullable=False),
        sa.Column('slot_minutes', sa.Integer, nullable=False, server_default='15'),
        sa.Column('max_patients', sa.Integer, nullable=False, server_default='0'),
        sa.UniqueConstraint('doctor_id','schedule_date','start_time','end_time', name='uq_doc_day_window')
    )

def downgrade():
    op.drop_table('doctor_schedules')
    op.drop_table('doctors')
    op.drop_index('ix_patients_uid', table_name='patients')
    op.drop_table('patients')
    op.drop_table('staff')