from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import require_roles, get_db
from app.utils.tenant import Tenant, get_tenant
from app.schemas.opd import (
    VisitCreate, VisitOutIDs, VisitListOut, VisitDetail,
)

from app.services.opd import OPDService
from datetime import datetime
router = APIRouter(prefix="/opd", tags=["OPD"])

@router.post("/visits", response_model=VisitOutIDs,
             dependencies=[Depends(require_roles("doctor","nurse","admin","branch_admin","superadmin"))])
def create_visit(payload: VisitCreate,
                 tenant: Tenant = Depends(get_tenant),
                 db: Session = Depends(get_db)):
    return OPDService(db, tenant).create_visit(payload)


@router.get("/visits", response_model=VisitListOut,
            dependencies=[Depends(require_roles("receptionist", "doctor", "nurse", "admin", "superadmin"))])
def list_visits(patient_id: int | None = None,
                doctor_id: int | None = None,
                date_from: str | None = None,
                date_to: str | None = None,
                appointment_id: int | None = None,
                page: int = 1, page_size: int = 20,
                tenant: Tenant = Depends(get_tenant),
                db: Session = Depends(get_db)):

    df = datetime.fromisoformat(date_from) if date_from else None
    dt = datetime.fromisoformat(date_to) if date_to else None
    items, total = OPDService(db, tenant).list_visits(patient_id, doctor_id, df, dt, page, page_size,appointment_id)
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.put(
    "/visits/{visit_id}",
    response_model=VisitDetail,
    dependencies=[Depends(require_roles(
        "receptionist", "doctor", "nurse", "admin", "superadmin"
    ))]
)
def update_visit(
        visit_id: int,
        payload: VisitCreate,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db)
):
    return OPDService(db, tenant).update_visit(visit_id, payload)


@router.get("/visits/{visit_id}", response_model=VisitDetail,
            dependencies=[Depends(require_roles("receptionist", "doctor", "nurse", "admin", "superadmin"))])
def get_visit(visit_id: int| None = None,
              appointment_id: int| None = None,
                  tenant: Tenant = Depends(get_tenant),
              db: Session = Depends(get_db)):
    return OPDService(db, tenant).get_visit(visit_id,appointment_id)


@router.post(
    "/opd/{visit_id}/vitals",
    dependencies=[Depends(require_roles("nurse","superadmin"))]
)
def add_vitals(
    visit_id: int,

    height_cm: int = Form(...),
    weight_kg: float = Form(...),
    temp_c: float | None = Form(None),
    bp_systolic: int | None = Form(None),
    bp_diastolic: int | None = Form(None),
    blood_sugar_bf: float = Form(...),
    blood_sugar_af: float = Form(...),


    pulse: int | None = Form(None),
    resp_rate: int | None = Form(None),
    spo2: int | None = Form(None),

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    return OPDService(db, tenant).add_vitals(
        visit_id,
        height_cm, weight_kg, temp_c,
        bp_systolic, bp_diastolic,
        pulse, resp_rate, spo2,blood_sugar_bf, blood_sugar_af,
    )



@router.put(
    "/opd/{visit_id}/vitals",
    dependencies=[Depends(require_roles("nurse","doctor","superadmin"))]
)
def update_vitals(
    visit_id: int,

    height_cm: int  = Form(...),
    weight_kg: float = Form(...),
    temp_c: float | None = Form(None),
    bp_systolic: int | None = Form(None),
    bp_diastolic: int | None = Form(None),
    blood_sugar_bf: float = Form(...),
    blood_sugar_af: float = Form(...),
    pulse: int | None = Form(None),
    resp_rate: int | None = Form(None),
    spo2: int | None = Form(None),

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    return OPDService(db, tenant).update_vitals(
        visit_id,
        height_cm,
        weight_kg,
        temp_c,
        bp_systolic,
        bp_diastolic,
        blood_sugar_bf,
        blood_sugar_af,
        pulse,
        resp_rate,
        spo2
    )



@router.delete(
    "/opd/{visit_id}/vitals",
    dependencies=[Depends(require_roles("nurse","admin","superadmin"))]
)
def delete_vitals(
    visit_id: int,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    return OPDService(db, tenant).delete_vitals(visit_id)