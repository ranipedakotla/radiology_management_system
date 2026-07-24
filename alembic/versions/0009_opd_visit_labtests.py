from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0009_opd_visit_labtests"
down_revision = "0008_entity_codes"  # <-- adjust if your last rev id differs
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "opd_visit_lab_tests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("visit_id", sa.Integer, sa.ForeignKey("opd_visits.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("test_name", sa.String(120), nullable=False),
        sa.Column("test_code", sa.String(50), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="Routine"),  # Routine/Urgent/Stat
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="prescribed"),  # prescribed/collected/posted
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade():
    op.drop_table("opd_visit_lab_tests")
