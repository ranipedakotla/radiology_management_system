from alembic import op
import sqlalchemy as sa

revision = "0014_add_created_by_to_ipd_discharges"
down_revision = "0012_ipd_admissions"
branch_labels = None
depends_on = None

def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(table) and any(c["name"] == col for c in insp.get_columns(table))

def upgrade():
    if not _has_column("ipd_discharges", "created_by_staff_id"):
        op.add_column(
            "ipd_discharges",
            sa.Column("created_by_staff_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_ipd_discharges_created_by_staff_id",
            "ipd_discharges",
            "staff",
            ["created_by_staff_id"],
            ["id"],
        )

def downgrade():
    # safe downgrade
    try:
        op.drop_constraint(
            "fk_ipd_discharges_created_by_staff_id",
            "ipd_discharges",
            type_="foreignkey",
        )
    except Exception:
        pass
    try:
        op.drop_column("ipd_discharges", "created_by_staff_id")
    except Exception:
        pass
