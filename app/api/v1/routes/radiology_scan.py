from datetime import datetime

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_scan import (
    RadiologyScanResponse,
)

from app.services.radiology_scan import (
    RadiologyScanService,
)

router = APIRouter(
    prefix="/radiology-scan",
    tags=["Radiology Scan"]
)


# ========================================
# START SCAN
# ========================================
@router.post(
    "/start",
    response_model=RadiologyScanResponse,
    status_code=201
)
def start_scan(

    registration_id: int = Form(...),

    technician_name: str | None = Form(
            default=None
        ),

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.start_scan(

        registration_id=registration_id,

        technician_name=technician_name,
    )


# ========================================
# GET ALL SCANS
# ========================================
@router.get(
    "/",
    response_model=list[RadiologyScanResponse]
)
def get_all_scans(

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.get_all_scans()


# ========================================
# GET SCAN BY ID
# ========================================
@router.get(
    "/{scan_id}",
    response_model=RadiologyScanResponse
)
def get_scan(

    scan_id: int,

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.get_scan(scan_id)


# ========================================
# COMPLETE SCAN
# ========================================
@router.put(
    "/{scan_id}/complete",
    response_model=RadiologyScanResponse
)
def complete_scan(

    scan_id: int,

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.complete_scan(scan_id)


# ========================================
# HOLD SCAN
# ========================================
@router.put(
    "/{scan_id}/hold",
    response_model=RadiologyScanResponse
)
def hold_scan(

    scan_id: int,

    hold_reason: str = Form(...),

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.hold_scan(

        scan_id=scan_id,

        hold_reason=hold_reason,
    )


# ========================================
# CANCEL SCAN
# ========================================
@router.put(
    "/{scan_id}/cancel",
    response_model=RadiologyScanResponse
)
def cancel_scan(

    scan_id: int,

    cancellation_reason: str = Form(...),

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.cancel_scan(

        scan_id=scan_id,

        cancellation_reason=cancellation_reason,
    )


# ========================================
# RESCHEDULE SCAN
# ========================================
@router.put(
    "/{scan_id}/reschedule",
    response_model=RadiologyScanResponse
)
def reschedule_scan(

    scan_id: int,

    reschedule_date: datetime = Form(...),

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.reschedule_scan(

        scan_id=scan_id,

        reschedule_date=reschedule_date,
    )


# ========================================
# GET SCAN BY REGISTRATION ID
# ========================================
@router.get(
    "/registration/{registration_id}",
    response_model=RadiologyScanResponse
)
def get_scan_by_registration(

    registration_id: int,

    db: Session = Depends(get_db)

):

    service = RadiologyScanService(db)

    return service.get_scan_by_registration(
        registration_id
    )
