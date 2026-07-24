from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles, get_db
from app.utils.tenant import Tenant, get_tenant
from app.schemas.ipd_master import (
    BulkFloorsIn, BulkBedTypesIn, BulkBedGroupsIn, BulkBedsIn, BulkResult, BedStatusItem
)
from app.services.ipd_master import IPDMasterService

router = APIRouter(prefix="/api/v1/ipd/master", tags=["IPD Master"])

@router.post("/floors/bulk", response_model=BulkResult,
             dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))])

def floors_bulk(payload: BulkFloorsIn,
                tenant: Tenant = Depends(get_tenant),
                db: Session = Depends(get_db)):
    c, u = IPDMasterService(db, tenant).bulk_upsert_floors([f.dict() for f in payload.floors])
    return {"created": c, "updated": u}

@router.post("/bed-types/bulk", response_model=BulkResult,
             dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))])
def bed_types_bulk(payload: BulkBedTypesIn,
                   tenant: Tenant = Depends(get_tenant),
                   db: Session = Depends(get_db)):
    c, u = IPDMasterService(db, tenant).bulk_upsert_bed_types([b.dict() for b in payload.bed_types])
    return {"created": c, "updated": u}

@router.post("/bed-groups/bulk", response_model=BulkResult,
             dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))])
def bed_groups_bulk(payload: BulkBedGroupsIn,
                    tenant: Tenant = Depends(get_tenant),
                    db: Session = Depends(get_db)):
    c, u = IPDMasterService(db, tenant).bulk_upsert_bed_groups([g.dict() for g in payload.bed_groups])
    return {"created": c, "updated": u}

@router.post("/beds/bulk", response_model=BulkResult,
             dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))])
def beds_bulk(payload: BulkBedsIn,
              tenant: Tenant = Depends(get_tenant),
              db: Session = Depends(get_db)):
    c, u = IPDMasterService(db, tenant).bulk_upsert_beds([b.dict() for b in payload.beds])
    return {"created": c, "updated": u}

@router.get("/beds/status", response_model=list[BedStatusItem],
            dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin", "receptionist"))])
def bed_status(tenant: Tenant = Depends(get_tenant),
               db: Session = Depends(get_db)):
    return IPDMasterService(db, tenant).bed_status_list()
