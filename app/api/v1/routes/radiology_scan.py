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
    prefix="/radiology-scans",
    tags=["Radiology Scan"]
)


# ========================================
# CREATE SCAN
# ========================================
@router.post(
    "/",
    response_model=RadiologyScanResponse,
    status_code=201
)
def create_radiology_scan(

    appointment_id: int = Form(...),

    technician_name: str | None = Form(
        default=None
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.create_scan(

        appointment_id=appointment_id,

        technician_name=technician_name,

        remarks=remarks,
    )


# ========================================
# GET ALL SCANS
# ========================================
@router.get(
    "/",
    response_model=list[
        RadiologyScanResponse
    ]
)
def get_all_radiology_scans(

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
def get_radiology_scan(

    scan_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.get_scan(
        scan_id
    )


# ========================================
# START SCAN
# ========================================
@router.put(
    "/{scan_id}/start",
    response_model=RadiologyScanResponse
)
def start_radiology_scan(

    scan_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.start_scan(
        scan_id
    )


# ========================================
# COMPLETE SCAN
# ========================================
@router.put(
    "/{scan_id}/complete",
    response_model=RadiologyScanResponse
)
def complete_radiology_scan(

    scan_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.complete_scan(
        scan_id
    )


# ========================================
# UPDATE SCAN
# ========================================
@router.put(
    "/{scan_id}",
    response_model=RadiologyScanResponse
)
def update_radiology_scan(

    scan_id: int,

    technician_name: str | None = Form(
        default=None
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.update_scan(

        scan_id=scan_id,

        technician_name=technician_name,

        remarks=remarks,
    )


# ========================================
# DELETE SCAN
# ========================================
@router.delete(
    "/{scan_id}"
)
def delete_radiology_scan(

    scan_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyScanService(db)

    return service.delete_scan(
        scan_id
    )