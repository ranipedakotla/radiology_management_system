from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_db, require_roles
from app.models.auth import User
from app.models.blood_bank import UserRole
from app.schemas.ambulance_billing import ResourceUsageResponse, BillingResponse
from app.services import ambulance_billing
from app.schemas.ambulance_billing import (
    ResourceUsageCreate,
    BillingCreate,
    InsuranceCreate, InsuranceResponse
)

router = APIRouter(prefix="/billing", tags=["Ambulance Billing"])


# ================== RESOURCE ==================

@router.post("/resource", response_model=ResourceUsageResponse)
def add_resource(data: ResourceUsageCreate, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

                 return ambulance_billing.add_resource(db, data)


@router.get("/resource/{request_id}", response_model=ResourceUsageResponse)
def get_resource(request_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

   return ambulance_billing.get_resource(db, request_id)


# ================== BILLING ==================

@router.post("/", response_model=BillingResponse)
def create_billing(data: BillingCreate, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_billing.create_billing(db, data)


@router.get("/{request_id}", response_model=BillingResponse)
def get_billing(request_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_billing.get_billing(db, request_id)


# ================== INSURANCE ==================

@router.post("/insurance", response_model=InsuranceResponse)
def create_insurance(data: InsuranceCreate, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):

    return ambulance_billing.create_insurance(db, data)


@router.get("/insurance/{billing_id}", response_model=InsuranceResponse)
def get_insurance(billing_id: int, db: Session = Depends(get_db),        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN],UserRole.RECEPTIONIST))):
    return ambulance_billing.get_insurance(db, billing_id)
