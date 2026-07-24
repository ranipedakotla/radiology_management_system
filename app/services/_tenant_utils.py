# app/services/_tenant_utils.py
from sqlalchemy import select
from app.utils.tenant import Tenant

# def _set_tenant_fields(obj, tenant: Tenant):
#     if hasattr(obj, "org_id"):
#         obj.org_id = tenant.org_id
#     if hasattr(obj, "hospital_id"):
#         obj.hospital_id = tenant.hospital_id
#     if hasattr(obj, "branch_id"):
#         obj.branch_id = tenant.branch_id\

def _set_tenant_fields(obj, tenant):
    if hasattr(obj, "hospital_id"):
        obj.hospital_id = getattr(tenant, "hospital_id", None) or getattr(tenant, "hid", None)

    if hasattr(obj, "branch_id"):
        obj.branch_id = getattr(tenant, "branch_id", None) or getattr(tenant, "bid", None)

    if hasattr(obj, "org_id"):
        obj.org_id = getattr(tenant, "org_id", None)


def _filter_by_tenant(stmt, model, tenant: Tenant):
    if hasattr(model, "org_id"):
        stmt = stmt.where(getattr(model, "org_id") == tenant.org_id)
    if hasattr(model, "branch_id"):
        stmt = stmt.where(getattr(model, "branch_id") == tenant.branch_id)
    return stmt

def _get_by_id_scoped(db, model, _id: int, tenant: Tenant):
    stmt = select(model).where(model.id == _id)
    stmt = _filter_by_tenant(stmt, model, tenant)
    return db.execute(stmt).scalar_one_or_none()
