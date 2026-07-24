from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta, datetime
import asyncio
from app.models.people import Patient
from app.core.security import get_db
from app.models.auth import User
from app.models.blood_bank import (
    Donor, BloodCollection, BloodInventory, BloodRequest,
    BloodStatus, RequestStatus,
    BloodTestReport, UserRole
)

from app.schemas.blood_bank import (
    DonorCreate, DonorResponse,
    BloodCollectionCreate, BloodCollectionResponse,
    BloodInventoryResponse,
    BloodRequestCreate, BloodRequestResponse,
    PatientCreate, PatientResponse,
    BloodTestReportCreate, BloodTestReportResponse,
    ComponentType, TestStatus, BloodInventoryLabUpdate
)
from fastapi import BackgroundTasks
from app.utils.blood_bank_permission import require_roles
from app.utils.blood_bank_email import send_email

router = APIRouter(prefix="/blood-bank", tags=["Blood Bank"])

MAX_RACK_CAPACITY = 100


# --------------------- HELPERS ---------------------

def update_expired_blood(db: Session):
    today = date.today()
    expired_units = db.query(BloodInventory).filter(
        BloodInventory.expiry_date < today,
        BloodInventory.status == BloodStatus.AVAILABLE
    ).all()
    for unit in expired_units:
        unit.status = BloodStatus.EXPIRED
        unit.is_expired = True
    if expired_units:
        db.commit()


def reserve_units(units, request, db: Session):
    for u in units:
        u.status = BloodStatus.RESERVED
    request.status = RequestStatus.APPROVED
    db.commit()


def check_rack_capacity(db: Session, rack: str):
    count = db.query(BloodInventory).filter(
        BloodInventory.storage_rack == rack,
        BloodInventory.status == BloodStatus.AVAILABLE
    ).count()
    if count >= MAX_RACK_CAPACITY:
        raise HTTPException(
            status_code=400,
            detail=f"Rack '{rack}' is full (capacity {MAX_RACK_CAPACITY})"
        )

# --------------------- DONORS ---------------------

@router.post("/donor", status_code=201)
def create_donor(
        donor: DonorCreate,
        db: Session = Depends(get_db),
        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN, UserRole.BLOOD_BANK_STAFF, UserRole.RECEPTIONIST]))
):
    # ================= EXCHANGE VALIDATION =================
    # If donor wants exchange → exchange blood group is required
    if donor.wants_exchange and not donor.exchange_blood_group:
        raise HTTPException(
            status_code=400,
            detail="exchange_blood_group required when wants_exchange is True"
        )

    # If donor does NOT want exchange → store NULL
    if not donor.wants_exchange:
        donor.exchange_blood_group = None

    # ================= DUPLICATE CHECK =================
    existing_donor = db.query(Donor).filter(
        (Donor.email == donor.email) | (Donor.phone == donor.phone)
    ).first()

    if existing_donor:
        raise HTTPException(
            status_code=400,
            detail=f"Donor already exists with email '{existing_donor.email}' or phone '{existing_donor.phone}'"
        )

    # ================= CREATE DONOR =================
    new_donor = Donor(
        first_name=donor.first_name,
        email=donor.email,
        phone=donor.phone,
        address=donor.address,
        blood_group=donor.blood_group,
        gender=donor.gender,
        age=donor.age,

        # Donation tracking
        last_donation_date=donor.last_donation_date,
        has_donated=False,

        # Exchange
        wants_exchange=donor.wants_exchange,
        exchange_blood_group=donor.exchange_blood_group,

        # Audit
        created_by=user.id
    )

    # ================= SAVE TO DB =================
    db.add(new_donor)
    db.commit()
    db.refresh(new_donor)

    # ================= RESPONSE =================
    return {
        "message": "Donor created successfully",
        "donor_id": new_donor.id,
        "exchange_blood_group": new_donor.exchange_blood_group
    }


@router.get("/donors", response_model=List[DonorResponse])
def get_donors(
        db: Session = Depends(get_db),
        user: User = Depends(require_roles([UserRole.ADMIN,UserRole.SUPERADMIN, UserRole.BLOOD_BANK_STAFF, UserRole.RECEPTIONIST]))
):
        return db.query(Donor).all()


@router.post("/eligibility/{donor_id}")
async def check_donor_eligibility(
        donor_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        user: User = Depends(require_roles([UserRole.DOCTOR,UserRole.RECEPTIONIST,UserRole.SUPERADMIN]))
):
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    today = date.today()
    reasons = []

    # Eligibility checks
    if donor.age < 18:
        reasons.append("Donor is under 18 years of age")
    if donor.last_donation_date:
        gap_days = (today - donor.last_donation_date).days
        if gap_days < 90:
            reasons.append(f"Minimum 90 days gap required (wait {90 - gap_days} more days)")

    donor.eligibility_checked_at = datetime.utcnow()
    donor.eligibility_checked_by = user.id

    if reasons:
        donor.eligibility = "NOT_ELIGIBLE"
        db.commit()
        subject = "Blood Donation Eligibility Update"
        body = f"""
Hello {donor.first_name},<br></br>
We checked your eligibility.<br>

Status: <b>NOT ELIGIBLE ❌</b><br>

Reason(s):<br>

{'<br>'.join(reasons)}


        Please
        try again later.


Blood
Bank
Team
"""
        background_tasks.add_task(send_email, subject, [donor.email], body)
        return {"donor_id": donor.id, "eligibility": donor.eligibility, "reasons": reasons}

    donor.eligibility = "ELIGIBLE"
    db.commit()
    subject = "You are Eligible to Donate Blood 🎉"
    body = f"""
Hello
{donor.first_name},

Good
news! You
are < b > ELIGIBLE < / b > to
donate
blood.

Thank
you
for helping save lives ❤

Blood
Bank
Team
"""
    background_tasks.add_task(send_email, subject, [donor.email], body)
    return {"donor_id": donor.id, "eligibility": donor.eligibility, "reasons": None}


# --------------------- PATIENTS ---------------------
#
# @router.post("/patients")
# def create_patient(
#     patient: PatientCreate,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_roles([UserRole.DOCTOR,UserRole.RECEPTIONIST]))
# ):
#     new_patient = Patient(**patient.dict(), created_by=current_user.id)
#     db.add(new_patient)
#     db.commit()
#     db.refresh(new_patient)
#     return {"message": "Patient created", "patient_id": new_patient.id}


# @router.get("/patients", response_model=List[PatientResponse])
# def get_patients(
#     db: Session = Depends(get_db),
#     user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR,UserRole.RECEPTIONIST]))
# ):
#     return db.query(Patient).all()

# --------------------- COLLECTION ---------------------


@router.post("/collections", response_model=BloodCollectionResponse)
def collect_blood(
    payload: BloodCollectionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BLOOD_BANK_STAFF,UserRole.SUPERADMIN]))
):
    donor = db.query(Donor).filter(Donor.id == payload.donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    if donor.eligibility != "ELIGIBLE":
        raise HTTPException(status_code=400, detail="Donor not eligible")

    collection_date = payload.collection_date or date.today()

    # Donation gap logic
    if donor.last_donation_date:
        days_passed = (collection_date - donor.last_donation_date).days
        required_gap = 120 if donor.gender.lower() == "female" else 90
        if days_passed < required_gap:
            raise HTTPException(
                status_code=400,
                detail=f"Donor must wait {required_gap - days_passed} more days to donate again"
            )

    # Create blood collection record
    collection = BloodCollection(
        donor_id=donor.id,
        collection_date=collection_date,
        test_status=TestStatus.PENDING
    )
    db.add(collection)

    # Update donor history
    donor.has_donated = True
    donor.last_donation_date = collection_date
    db.commit()
    db.refresh(collection)

    # Send email in background
    subject = "Blood Donation Successful"
    body = f"""
Hello
{donor.first_name},

Your
blood
donation
on
{collection_date}
was
successful.

Blood
Bank
Team
"""
    background_tasks.add_task(send_email, subject, [donor.email], body)

    return collection


# --------------------- TEST ---------------------

@router.post("/tests", response_model=BloodTestReportResponse)
def add_test(
    payload: BloodTestReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(
        require_roles([
            UserRole.ADMIN,
            UserRole.LAB_TECH,
            UserRole.SUPERADMIN
        ])
    )
):
    # Check duplicate report
    existing = db.query(BloodTestReport).filter(
        BloodTestReport.collection_id == payload.collection_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Test report already exists"
        )

    # Get collection
    collection = db.query(BloodCollection).filter(
        BloodCollection.id == payload.collection_id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=404,
            detail="Collection not found"
        )

    donor = collection.donor

    # Determine test result
    reasons = []

    if payload.hiv:
        reasons.append("HIV Positive")

    if payload.hbv:
        reasons.append("HBV Positive")

    if payload.hcv:
        reasons.append("HCV Positive")

    if payload.malaria:
        reasons.append("Malaria Positive")

    if payload.syphilis:
        reasons.append("Syphilis Positive")

    failed = len(reasons) > 0

    # Update collection status
    if failed:
        collection.test_status = TestStatus.REJECTED
        collection.rejection_reason = ", ".join(reasons)

        # Mark donor ineligible
        donor.eligibility = "NOT_ELIGIBLE"

    else:
        collection.test_status = TestStatus.AVAILABLE
        collection.rejection_reason = None

    # Create report
    test = BloodTestReport(
        collection_id=payload.collection_id,
        hiv=payload.hiv,
        hbv=payload.hbv,
        hcv=payload.hcv,
        malaria=payload.malaria,
        syphilis=payload.syphilis,
        eligibility=not failed,
        rejection_reason=", ".join(reasons) if reasons else None,
        tested_by=user.id,
        test_date=payload.test_date or datetime.utcnow()
    )

    db.add(test)

    # Prevent duplicate inventory
    existing_inventory = db.query(BloodInventory).filter(
        BloodInventory.collection_id == collection.id
    ).first()

    if existing_inventory:
        raise HTTPException(
            status_code=400,
            detail="Inventory already exists for this collection"
        )

    if not failed:
        expiry_days = {
            "RBC": 42,
            "PLATELETS": 5,
            "PLASMA": 365
        }

        for component in ComponentType:
            db.add(
                BloodInventory(
                    collection_id=collection.id,
                    blood_group=donor.blood_group,
                    component_type=component,
                    status=BloodStatus.PENDING_LAB,
                    quantity_ml=None,
                    storage_rack=None,
                    expiry_date=date.today()
                    + timedelta(days=expiry_days[component.value]),
                    is_expired=False
                )
            )

    else:
        for component in ComponentType:
            db.add(
                BloodInventory(
                    collection_id=collection.id,
                    blood_group=donor.blood_group,
                    component_type=component,
                    status=BloodStatus.DISCARDED,
                    quantity_ml=None,
                    storage_rack=None,
                    expiry_date=date.today(),  # avoid NULL error
                    is_expired=True
                )
            )

    db.commit()
    db.refresh(test)

    return test

# --------------------- LAB UPDATE ---------------------

@router.put("/stock/{inventory_id}/lab-update", response_model=BloodInventoryResponse)
def lab_update_stock(
    inventory_id: int,
    payload: BloodInventoryLabUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.LAB_TECH,UserRole.SUPERADMIN]))
):
    inventory = db.query(BloodInventory).filter(BloodInventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Stock item not found")

    check_rack_capacity(db, payload.storage_rack)

    inventory.quantity_ml = payload.quantity_ml
    inventory.storage_rack = payload.storage_rack
    inventory.status = BloodStatus.AVAILABLE
    db.commit()
    db.refresh(inventory)
    return inventory


@router.get("/stock", response_model=List[BloodInventoryResponse])
def get_stock(
    blood_group: Optional[str] = Query(None),
    component_type: Optional[str] = Query(None),
    status: Optional[BloodStatus] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BLOOD_BANK_STAFF, UserRole.DOCTOR,UserRole.SUPERADMIN]))
):
    query = db.query(BloodInventory)
    if not status:
        query = query.filter(BloodInventory.status.in_([BloodStatus.AVAILABLE, BloodStatus.PENDING_LAB]))
    else:
        query = query.filter(BloodInventory.status == status)
    if blood_group:
        query = query.filter(BloodInventory.blood_group == blood_group.upper())
    if component_type:
        query = query.filter(BloodInventory.component_type == component_type.upper())
    query = query.order_by(BloodInventory.created_at.desc())
    return query.all()


def match_exchange_request(db: Session, request: BloodRequest):
    if request.matched_request_id or request.matched_donor_id:
        return None

    opposite_request = db.query(BloodRequest).filter(
        BloodRequest.id != request.id,
        BloodRequest.status == RequestStatus.PENDING,
        BloodRequest.allow_exchange == True,
        BloodRequest.blood_group == request.exchange_blood_group,
        BloodRequest.exchange_blood_group == request.blood_group,
        BloodRequest.component_type == request.component_type
    ).first()

    if not opposite_request:
        return None

    request.matched_request_id = opposite_request.id
    opposite_request.matched_request_id = request.id
    request.status = RequestStatus.MATCHED
    opposite_request.status = RequestStatus.MATCHED

    db.commit()
    return opposite_request  # ← returns full object



@router.post("/blood/request", response_model=BloodRequestResponse)
def request_blood(
    request: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.DOCTOR, UserRole.RECEPTIONIST, UserRole.SUPERADMIN]))
):
    # 1️⃣ Validate patient
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if request.allow_exchange and not request.exchange_blood_group:
        raise HTTPException(
            status_code=400,
            detail="exchange_blood_group required when allow_exchange is True"
        )

    # 2️⃣ Create blood request
    blood_request = BloodRequest(
        patient_id=patient.id,
        blood_group=request.blood_group,
        exchange_blood_group=request.exchange_blood_group,
        component_type=request.component_type,
        units_required=request.units_required,
        allow_exchange=request.allow_exchange,
        status=RequestStatus.PENDING,
        requested_by=current_user.id
    )
    db.add(blood_request)
    db.commit()
    db.refresh(blood_request)

    required_ml = blood_request.units_required * 450

    # 3️⃣ Try P→P exchange match
    if blood_request.allow_exchange:
        opposite_request = db.query(BloodRequest).filter(
            BloodRequest.id != blood_request.id,
            BloodRequest.status == RequestStatus.PENDING,
            BloodRequest.allow_exchange == True,
            # Patient B needs what Patient A offers, and offers what Patient A needs
            BloodRequest.blood_group == blood_request.exchange_blood_group,
            BloodRequest.exchange_blood_group == blood_request.blood_group,
            BloodRequest.component_type == blood_request.component_type
        ).first()

        if opposite_request:
            # Link both requests to each other
            blood_request.matched_request_id = opposite_request.id
            opposite_request.matched_request_id = blood_request.id
            blood_request.status = RequestStatus.MATCHED
            opposite_request.status = RequestStatus.MATCHED

            # Reserve stock for Patient A (from opposite patient's donated blood group)
            stock_for_a = db.query(BloodInventory).join(BloodCollection).filter(
                BloodInventory.blood_group == blood_request.exchange_blood_group,
                BloodInventory.component_type == blood_request.component_type,
                BloodInventory.status == BloodStatus.AVAILABLE,
                BloodInventory.quantity_ml >= required_ml
            ).first()
            if stock_for_a:
                stock_for_a.status = BloodStatus.RESERVED

            # Reserve stock for Patient B (from current patient's donated blood group)
            stock_for_b = db.query(BloodInventory).join(BloodCollection).filter(
                BloodInventory.blood_group == opposite_request.exchange_blood_group,
                BloodInventory.component_type == opposite_request.component_type,
                BloodInventory.status == BloodStatus.AVAILABLE,
                BloodInventory.quantity_ml >= (opposite_request.units_required * 450)
            ).first()
            if stock_for_b:
                stock_for_b.status = BloodStatus.RESERVED

            db.commit()
            db.refresh(blood_request)

            return BloodRequestResponse(
                id=blood_request.id,
                patient_id=blood_request.patient_id,
                blood_group=blood_request.blood_group,
                exchange_blood_group=blood_request.exchange_blood_group,
                component_type=blood_request.component_type,
                units_required=blood_request.units_required,
                allow_exchange=blood_request.allow_exchange,
                status=blood_request.status,
                matched_request_id=blood_request.matched_request_id,
                matched_donor_id=blood_request.matched_donor_id
            )

    # 4️⃣ Try P→Donor match (direct donor stock)
    donor_stock = db.query(BloodInventory).filter(
        BloodInventory.blood_group == blood_request.blood_group,
        BloodInventory.component_type == blood_request.component_type,
        BloodInventory.status == BloodStatus.AVAILABLE,
        BloodInventory.quantity_ml >= required_ml
    ).first()

    if donor_stock:
        donor_stock.status = BloodStatus.RESERVED

        # Find which donor this stock belongs to
        collection = db.query(BloodCollection).filter(
            BloodCollection.id == donor_stock.collection_id
        ).first()
        if collection:
            blood_request.matched_donor_id = collection.donor_id

        blood_request.status = RequestStatus.MATCHED
        db.commit()
        db.refresh(blood_request)

    return BloodRequestResponse(
        id=blood_request.id,
        patient_id=blood_request.patient_id,
        blood_group=blood_request.blood_group,
        exchange_blood_group=blood_request.exchange_blood_group,
        component_type=blood_request.component_type,
        units_required=blood_request.units_required,
        allow_exchange=blood_request.allow_exchange,
        status=blood_request.status,
        matched_request_id=blood_request.matched_request_id,
        matched_donor_id=blood_request.matched_donor_id
    )


@router.get("/requests", response_model=List[BloodRequestResponse])
def list_requests(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.BLOOD_BANK_STAFF,UserRole.SUPERADMIN]))
):
    query = db.query(BloodRequest)
    if from_date:
        from_datetime = datetime.combine(from_date, datetime.min.time())
        query = query.filter(BloodRequest.created_at >= from_datetime)

    if to_date:
        to_datetime = datetime.combine(to_date, datetime.max.time())
        query = query.filter(BloodRequest.created_at <= to_datetime)

    query = query.order_by(BloodRequest.created_at.desc())
    return query.all()


@router.post("/issue/{request_id}")
def issue_blood(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BLOOD_BANK_STAFF, UserRole.SUPERADMIN]))
):
    blood_request = db.query(BloodRequest).filter(
        BloodRequest.id == request_id,
        BloodRequest.status.in_([RequestStatus.PENDING, RequestStatus.MATCHED])
    ).first()

    if not blood_request:
        raise HTTPException(status_code=404, detail="Request not found or already processed")

    required_ml = blood_request.units_required * 450

    # ================== 🔄 P→P EXCHANGE FLOW ==================
    if blood_request.status == RequestStatus.MATCHED and blood_request.matched_request_id:

        stock = db.query(BloodInventory).filter(
            BloodInventory.blood_group == blood_request.exchange_blood_group,
            BloodInventory.component_type == blood_request.component_type,
            BloodInventory.status.in_([BloodStatus.RESERVED, BloodStatus.AVAILABLE]),
            BloodInventory.quantity_ml >= required_ml
        ).first()

        if not stock:
            raise HTTPException(
                status_code=400,
                detail="Exchange stock not found for this request"
            )

        stock.quantity_ml -= required_ml
        if stock.quantity_ml == 0:
            stock.status = BloodStatus.ISSUED

        blood_request.status = RequestStatus.ISSUED
        db.commit()

        return {
            "message": "Blood issued via P→P exchange",
            "source": "exchange",
            "blood_group_issued": blood_request.exchange_blood_group,
            "issued_ml": required_ml,
            "remaining_stock_ml": stock.quantity_ml,
            "request_status": blood_request.status
        }

    # ==================  P→DONOR DIRECT FLOW ==================
    if blood_request.status == RequestStatus.MATCHED and blood_request.matched_donor_id:

        stock = db.query(BloodInventory).filter(
            BloodInventory.blood_group == blood_request.blood_group,
            BloodInventory.component_type == blood_request.component_type,
            BloodInventory.status.in_([BloodStatus.RESERVED, BloodStatus.AVAILABLE]),
            BloodInventory.quantity_ml >= required_ml
        ).first()

        if not stock:
            raise HTTPException(
                status_code=400,
                detail="No stock available for this request"
            )

        stock.quantity_ml -= required_ml
        if stock.quantity_ml == 0:
            stock.status = BloodStatus.ISSUED

        blood_request.status = RequestStatus.ISSUED
        db.commit()

        return {
            "message": "Blood issued from donor stock",
            "source": "donor",
            "blood_group_issued": blood_request.blood_group,
            "issued_ml": required_ml,
            "remaining_stock_ml": stock.quantity_ml,
            "request_status": blood_request.status
        }

    # ================== 🔵 PENDING → NORMAL STOCK FLOW ==================
    if blood_request.status == RequestStatus.PENDING:

        stock = db.query(BloodInventory).filter(
            BloodInventory.blood_group == blood_request.blood_group,
            BloodInventory.component_type == blood_request.component_type,
            BloodInventory.status == BloodStatus.AVAILABLE,
            BloodInventory.quantity_ml >= required_ml
        ).first()

        if not stock:
            blood_request.status = RequestStatus.REJECTED
            db.commit()
            raise HTTPException(status_code=400, detail="No stock available — request rejected")

        stock.quantity_ml -= required_ml
        if stock.quantity_ml == 0:
            stock.status = BloodStatus.ISSUED

        blood_request.status = RequestStatus.ISSUED
        db.commit()

        return {
            "message": "Blood issued from normal stock",
            "source": "normal",
            "blood_group_issued": blood_request.blood_group,
            "issued_ml": required_ml,
            "remaining_stock_ml": stock.quantity_ml,
            "request_status": blood_request.status
        }

    # ==================  NO MATCH FOUND ==================
    blood_request.status = RequestStatus.REJECTED
    db.commit()
    raise HTTPException(status_code=400, detail="No matched stock found — request rejected")