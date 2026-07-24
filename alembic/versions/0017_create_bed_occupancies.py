from alembic import op
import sqlalchemy as sa

revision = "0017_create_bed_occupancies"
down_revision = "0016_tenantize_models"
branch_labels = None
depends_on = None

def upgrade():
    insp = sa.inspect(op.get_bind())
    if not insp.has_table("bed_occupancies"):
        op.create_table(
            "bed_occupancies",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("admission_id", sa.Integer, nullable=False),
            sa.Column("bed_id", sa.Integer, nullable=False),
            sa.Column("start", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("end", sa.DateTime, nullable=True),

            # tenant columns
            sa.Column("hospital_id", sa.Integer, nullable=True),
            sa.Column("branch_id", sa.Integer, nullable=True),
        )
        # FKs
        op.create_foreign_key("fk_bedocc_adm", "bed_occupancies", "ipd_admissions", ["admission_id"], ["id"])
        op.create_foreign_key("fk_bedocc_bed", "bed_occupancies", "beds", ["bed_id"], ["id"])
        op.create_foreign_key("fk_bedocc_hosp", "bed_occupancies", "hospitals", ["hospital_id"], ["id"])
        op.create_foreign_key("fk_bedocc_branch", "bed_occupancies", "branches", ["branch_id"], ["id"])

        # indexes
        op.create_index("ix_bedocc_admission", "bed_occupancies", ["admission_id"])
        op.create_index("ix_bedocc_bed", "bed_occupancies", ["bed_id"])
        op.create_index("ix_bedocc_branch", "bed_occupancies", ["branch_id"])

def downgrade():
    insp = sa.inspect(op.get_bind())
    if insp.has_table("bed_occupancies"):
        op.drop_table("bed_occupancies")
