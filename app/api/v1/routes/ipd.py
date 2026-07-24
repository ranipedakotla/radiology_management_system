from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.security import require_roles, get_current_user, get_db
from app.schemas.ipd import AdmitIn, TransferIn, DischargeIn, AdmissionOut, AdmissionListOut
from app.services.ipd import IPDService
from app.utils.tenant import Tenant, get_tenant

router = APIRouter(prefix="/ipd", tags=["IPD"])

@router.post("/admissions", response_model=AdmissionOut)
def admit(payload: AdmitIn,
          user = Depends(get_current_user),
          tenant: Tenant = Depends(get_tenant),
          db: Session = Depends(get_db)):
    require_roles("receptionist","admin","superadmin","nurse")(user)
    return IPDService(db, tenant).admit(payload, created_by_user_id=user.id)

@router.get("/admissions", response_model=AdmissionListOut,
            dependencies=[Depends(require_roles("receptionist","admin","superadmin","nurse","doctor","branch_admin"))])
def list_admissions(page: int = 1, page_size: int = 20,
                    tenant: Tenant = Depends(get_tenant),
                    db: Session = Depends(get_db)):
    return IPDService(db, tenant).list_admissions(page, page_size)

@router.get("/admissions/{admission_id}", response_model=AdmissionOut,
            dependencies=[Depends(require_roles("receptionist","admin","superadmin","nurse","doctor","branch_admin"))])
def get_admission(admission_id: int,
                  tenant: Tenant = Depends(get_tenant),
                  db: Session = Depends(get_db)):
    return IPDService(db, tenant).get_admission(admission_id)

@router.post("/admissions/{admission_id}/transfer", response_model=AdmissionOut)
def transfer(admission_id: int, payload: TransferIn,
             user = Depends(get_current_user),
             tenant: Tenant = Depends(get_tenant),
             db: Session = Depends(get_db)):
    require_roles("receptionist","admin","superadmin","nurse")(user)
    return IPDService(db, tenant).transfer(admission_id, payload, created_by_user_id=user.id)

@router.post("/admissions/{admission_id}/discharge", response_model=AdmissionOut)
def discharge(admission_id: int, payload: DischargeIn,
              user = Depends(get_current_user),
              tenant: Tenant = Depends(get_tenant),
              db: Session = Depends(get_db)):
    require_roles("receptionist","admin","superadmin","nurse")(user)
    return IPDService(db, tenant).discharge(admission_id, payload, created_by_user_id=user.id)
