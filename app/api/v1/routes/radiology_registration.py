from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_registration import (
    RadiologyRegistrationResponse,
)

from app.services.radiology_registration import (
    RadiologyRegistrationService,
)


router = APIRouter(
    prefix="/radiology-registrations",
    tags=["Radiology Registration"]
)


# ========================================
# CREATE RADIOLOGY REGISTRATION
# ========================================
@router.post(
    "/",
    response_model=RadiologyRegistrationResponse,
    status_code=201
)
def create_radiology_registration(

    patient_id: int | None = Form(default=None),

    external_id: int | None = Form(default=None),

    test_name: str = Form(...),

    test_category: str | None = Form(default=None),

    doctor_name: str | None = Form(default=None),

    db: Session = Depends(get_db)

):

    service = RadiologyRegistrationService(db)

    return service.create_registration(
        patient_id=patient_id,
        external_id=external_id,
        test_name=test_name,
        test_category=test_category,
        doctor_name=doctor_name,
    )


# ========================================
# GET ALL RADIOLOGY REGISTRATIONS
# ========================================
@router.get(
    "/",
    response_model=list[RadiologyRegistrationResponse]
)
def get_all_radiology_registrations(

    db: Session = Depends(get_db)

):

    service = RadiologyRegistrationService(db)

    return service.get_all_registrations()


# ========================================
# GET REGISTRATION BY ID
# ========================================
@router.get(
    "/{registration_id}",
    response_model=RadiologyRegistrationResponse
)
def get_radiology_registration(

    registration_id: int,

    db: Session = Depends(get_db)

):

    service = RadiologyRegistrationService(db)

    return service.get_registration(
        registration_id
    )


# ========================================
# UPDATE REGISTRATION
# ========================================
@router.put(
    "/{registration_id}",
    response_model=RadiologyRegistrationResponse
)
def update_radiology_registration(

    registration_id: int,

    test_name: str | None = Form(default=None),

    test_category: str | None = Form(default=None),

    doctor_name: str | None = Form(default=None),

    status: str | None = Form(default=None),

    scan_status: str | None = Form(default=None),

    db: Session = Depends(get_db)

):

    service = RadiologyRegistrationService(db)

    return service.update_registration(

        registration_id=registration_id,

        test_name=test_name,

        test_category=test_category,

        doctor_name=doctor_name,

        status=status,

        scan_status=scan_status,
    )


# ========================================
# DELETE REGISTRATION
# ========================================
@router.delete(
    "/{registration_id}"
)
def delete_radiology_registration(

    registration_id: int,

    db: Session = Depends(get_db)

):

    service = RadiologyRegistrationService(db)

    return service.delete_registration(
        registration_id
    )