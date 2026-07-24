from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0008_ipd_master"
down_revision = "0011_ipd_basic"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "floors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text),
    )
    op.create_table(
        "bed_types",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(60), nullable=False, unique=True, index=True),
    )
    op.create_table(
        "bed_groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, index=True),
        sa.Column("description", sa.Text),
        sa.Column("floor_id", sa.Integer, sa.ForeignKey("floors.id"), nullable=False, index=True),
    )
    op.create_table(
        "beds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True, index=True),
        sa.Column("bed_type_id", sa.Integer, sa.ForeignKey("bed_types.id"), nullable=False, index=True),
        sa.Column("bed_group_id", sa.Integer, sa.ForeignKey("bed_groups.id"), nullable=False, index=True),
        sa.Column("is_occupied", sa.Boolean, nullable=False, server_default=sa.text("0")),
    )

def downgrade():
    op.drop_table("beds")
    op.drop_table("bed_groups")
    op.drop_table("bed_types")
    op.drop_table("floors")
