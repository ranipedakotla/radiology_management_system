# alembic/versions/0016_tenantize_models.py
from alembic import op
import sqlalchemy as sa

revision = "0016_tenantize_models"
down_revision = "0015_multi_branch_rbac"
branch_labels = None
depends_on = None

TENANTED_TABLES = [
    # people
    "patients", "staff", "doctors",
    # schedule
    "doctor_schedules",
    # opd
    "opd_visits", "opd_visit_diagnoses", "prescriptions", "prescription_items", "opd_visit_lab_tests",
    # appointments
    "appointments",
    # billing
    "invoices", "invoice_items", "receipts",
    # ipd masters
    "floors", "bed_types", "bed_groups", "beds",
    # ipd runtime (some may not exist yet in your DB; we'll skip if missing)
    "ipd_admissions", "ipd_transfers", "ipd_discharges", "bed_occupancies",
]

def _insp():
    return sa.inspect(op.get_bind())

def _table_exists(name: str) -> bool:
    try:
        return _insp().has_table(name)
    except Exception:
        return False

def _safe_get(fn, default):
    try:
        return fn()
    except Exception:
        return default

def _cols(table):
    if not _table_exists(table):
        return set()
    return {c["name"] for c in _safe_get(lambda: _insp().get_columns(table), [])}

def _indexes(table):
    if not _table_exists(table):
        return set()
    return {ix["name"] for ix in _safe_get(lambda: _insp().get_indexes(table), [])}

def _fks(table):
    if not _table_exists(table):
        return {}
    fks = _safe_get(lambda: _insp().get_foreign_keys(table), [])
    return {fk.get("name") or "": set(fk.get("constrained_columns") or []) for fk in fks}

def _uniques(table):
    if not _table_exists(table):
        return []
    uqs = _safe_get(lambda: _insp().get_unique_constraints(table), [])
    return [{"name": uq.get("name"), "cols": tuple(uq.get("column_names") or [])} for uq in uqs]

def _has_uc_by_cols(table, cols_tuple):
    cols_tuple = tuple(cols_tuple)
    return any(uq["cols"] == cols_tuple for uq in _uniques(table))

def _drop_uc_by_cols(table, cols_tuple):
    cols_tuple = tuple(cols_tuple)
    for uq in _uniques(table):
        if uq["cols"] == cols_tuple:
            if uq["name"]:
                try:
                    op.drop_constraint(uq["name"], table, type_="unique")
                except Exception:
                    pass
            return

def _safe_add_tenant_columns(table):
    if not _table_exists(table):
        return
    existing = _cols(table)
    with op.batch_alter_table(table) as b:
        if "hospital_id" not in existing:
            b.add_column(sa.Column("hospital_id", sa.Integer(), nullable=True))
        if "branch_id" not in existing:
            b.add_column(sa.Column("branch_id", sa.Integer(), nullable=True))

    idxs = _indexes(table)
    if "hospital_id" in _cols(table) and f"ix_{table}_hospital_id" not in idxs:
        try:
            op.create_index(f"ix_{table}_hospital_id", table, ["hospital_id"])
        except Exception:
            pass
    if "branch_id" in _cols(table) and f"ix_{table}_branch_id" not in idxs:
        try:
            op.create_index(f"ix_{table}_branch_id", table, ["branch_id"])
        except Exception:
            pass

    fks = _fks(table)
    if "hospital_id" in _cols(table) and not any(cols == {"hospital_id"} for cols in fks.values()):
        try:
            op.create_foreign_key(f"fk_{table}_hospital", table, "hospitals", ["hospital_id"], ["id"])
        except Exception:
            pass
    if "branch_id" in _cols(table) and not any(cols == {"branch_id"} for cols in fks.values()):
        try:
            op.create_foreign_key(f"fk_{table}_branch", table, "branches", ["branch_id"], ["id"])
        except Exception:
            pass

def upgrade():
    # 1) add tenant columns wherever the table exists
    for t in TENANTED_TABLES:
        _safe_add_tenant_columns(t)

    # 2) staff.user_id -> users.id (only if staff table exists)
    if _table_exists("staff"):
        try:
            with op.batch_alter_table("staff") as b:
                for cand in ("staff_user_id_fkey", "fk_staff_user"):
                    try:
                        b.drop_constraint(cand, type_="foreignkey")
                    except Exception:
                        pass
                b.create_foreign_key("fk_staff_user", "users", ["user_id"], ["id"])
        except Exception:
            pass

    # 3) composite uniques (guarded)
    if _table_exists("patients"):
        _drop_uc_by_cols("patients", ("patient_code",))
        _drop_uc_by_cols("patients", ("patient_uid",))
        if not _has_uc_by_cols("patients", ("hospital_id", "patient_uid")) and \
           {"hospital_id", "patient_uid"}.issubset(_cols("patients")):
            op.create_unique_constraint("uq_patients_hosp_uid", "patients", ["hospital_id", "patient_uid"])
        if not _has_uc_by_cols("patients", ("branch_id", "patient_code")) and \
           {"branch_id", "patient_code"}.issubset(_cols("patients")):
            op.create_unique_constraint("uq_patients_branch_code", "patients", ["branch_id", "patient_code"])

    if _table_exists("staff") and \
       not _has_uc_by_cols("staff", ("branch_id", "staff_code")) and \
       {"branch_id", "staff_code"}.issubset(_cols("staff")):
        op.create_unique_constraint("uq_staff_branch_code", "staff", ["branch_id", "staff_code"])

    if _table_exists("doctors"):
        _drop_uc_by_cols("doctors", ("doctor_code",))
        if not _has_uc_by_cols("doctors", ("branch_id", "doctor_code")) and \
           {"branch_id", "doctor_code"}.issubset(_cols("doctors")):
            op.create_unique_constraint("uq_doctors_branch_code", "doctors", ["branch_id", "doctor_code"])

    if _table_exists("beds") and \
       not _has_uc_by_cols("beds", ("branch_id", "code")) and \
       {"branch_id", "code"}.issubset(_cols("beds")):
        op.create_unique_constraint("uq_bed_branch_code", "beds", ["branch_id", "code"])

    for t, col, uqname in [
        ("floors", "name", "uq_floor_branch_name"),
        ("bed_types", "name", "uq_bedtype_branch_name"),
        ("bed_groups", "name", "uq_bedgroup_branch_name"),
    ]:
        if _table_exists(t) and not _has_uc_by_cols(t, ("branch_id", col)) and \
           {"branch_id", col}.issubset(_cols(t)):
            op.create_unique_constraint(uqname, t, ["branch_id", col])

    if _table_exists("invoices") and not _has_uc_by_cols("invoices", ("branch_id", "invoice_no")) and \
       {"branch_id", "invoice_no"}.issubset(_cols("invoices")):
        op.create_unique_constraint("uq_invoices_branch_no", "invoices", ["branch_id", "invoice_no"])

    if _table_exists("ipd_admissions") and not _has_uc_by_cols("ipd_admissions", ("branch_id", "admission_no")) and \
       {"branch_id", "admission_no"}.issubset(_cols("ipd_admissions")):
        op.create_unique_constraint("uq_ipd_branch_admno", "ipd_admissions", ["branch_id", "admission_no"])

    if _table_exists("opd_visits") and not _has_uc_by_cols("opd_visits", ("branch_id", "visit_no")) and \
       {"branch_id", "visit_no"}.issubset(_cols("opd_visits")):
        op.create_unique_constraint("uq_opd_branch_visitno", "opd_visits", ["branch_id", "visit_no"])

def downgrade():
    pass
