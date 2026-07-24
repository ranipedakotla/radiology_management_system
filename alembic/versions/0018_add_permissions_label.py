# alembic/versions/0017_add_permissions_label.py
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0018_add_permissions_label"
down_revision = "0017_create_bed_occupancies"   # <-- keep this matching your previous head
branch_labels = None
depends_on = None

def _has_column(table_name: str, col_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return col_name in cols

def upgrade():
    # add label column if missing
    if not _has_column("permissions", "label"):
        op.add_column("permissions", sa.Column("label", sa.String(length=120), nullable=True))
        # backfill label with code for existing rows
        op.execute("UPDATE permissions SET label = code WHERE label IS NULL")

def downgrade():
    # drop if present (safe for dev)
    if _has_column("permissions", "label"):
        op.drop_column("permissions", "label")
