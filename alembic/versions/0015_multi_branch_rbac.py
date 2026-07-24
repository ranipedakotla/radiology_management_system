from alembic import op
import sqlalchemy as sa

revision = "0015_multi_branch_rbac"
down_revision = "0014_add_created_by_to_ipd_discharges"
branch_labels = None
depends_on = None

def _has_table(name): return sa.inspect(op.get_bind()).has_table(name)
def _has_col(t, c):
    insp = sa.inspect(op.get_bind())
    return insp.has_table(t) and any(x["name"] == c for x in insp.get_columns(t))

def upgrade():
    bind = op.get_bind()

    # 1) branches
    if not _has_table("branches"):
        op.create_table(
            "branches",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("hospital_id", sa.Integer, sa.ForeignKey("hospitals.id")),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("code", sa.String(20), nullable=False, unique=True),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("1")),
        )
        op.create_index("ix_branches_hospital_id", "branches", ["hospital_id"])

    # 2) users: tenant fields + user_branches
    if _has_table("users"):
        if not _has_col("users", "hospital_id"):
            op.add_column("users", sa.Column("hospital_id", sa.Integer, sa.ForeignKey("hospitals.id")))
            op.create_index("ix_users_hospital_id", "users", ["hospital_id"])
        if not _has_col("users", "current_branch_id"):
            op.add_column("users", sa.Column("current_branch_id", sa.Integer, sa.ForeignKey("branches.id")))
            op.create_index("ix_users_current_branch_id", "users", ["current_branch_id"])

    if not _has_table("user_branches"):
        op.create_table(
            "user_branches",
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
            sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id"), primary_key=True),
        )

    # 3) RBAC (create only if missing)
    if not _has_table("roles"):
        op.create_table("roles",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(80), unique=True, index=True))
    if not _has_table("permissions"):
        op.create_table("permissions",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(80), unique=True, index=True),
            sa.Column("description", sa.String(255)))
    if not _has_table("user_roles"):
        op.create_table("user_roles",
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
            sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id"), primary_key=True))
    if not _has_table("role_permissions"):
        op.create_table("role_permissions",
            sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id"), primary_key=True),
            sa.Column("permission_id", sa.Integer, sa.ForeignKey("permissions.id"), primary_key=True))

    # 4) tenantize domain tables (adjust list to your project)
    tenantize = [
        "patients", "staff", "doctors", "doctor_schedules",
        "appointments", "opd_visits",
        "ipd_admissions", "ipd_transfers", "ipd_discharges",
        "lab_tests_catalog", "lab_samples", "lab_results",
        "rad_orders", "rad_reports",
        "invoices", "invoice_items", "receipts",
        "po_headers", "po_items", "grn_headers", "grn_items", "stock_ledger",
    ]
    for t in tenantize:
        if _has_table(t):
            if not _has_col(t, "hospital_id"):
                op.add_column(t, sa.Column("hospital_id", sa.Integer, sa.ForeignKey("hospitals.id")))
                op.create_index(f"ix_{t}_hospital_id", t, ["hospital_id"])
            if not _has_col(t, "branch_id"):
                op.add_column(t, sa.Column("branch_id", sa.Integer, sa.ForeignKey("branches.id")))
                op.create_index(f"ix_{t}_branch_id", t, ["branch_id"])

    # 5) appointments: avoid double booking per branch
    if _has_table("appointments"):
        try:
            op.create_index("ix_appt_branch_time", "appointments", ["branch_id", "scheduled_for"])
        except Exception:
            pass
        try:
            op.create_unique_constraint(
                "uq_appt_branch_doctor_time", "appointments",
                ["branch_id", "doctor_id", "scheduled_for"])
        except Exception:
            pass

def downgrade():
    pass
