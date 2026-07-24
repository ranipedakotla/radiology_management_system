from datetime import date, time

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_appointment import (
    RadiologyAppointmentResponse,
)

from app.services.radiology_appointment import (
    RadiologyAppointmentService,
)

router = APIRouter(
    prefix="/radiology-appointments",
    tags=["Radiology Appointment"]
)

# ========================================
# CREATE APPOINTMENT
# ========================================
@router.post(
    "/",
    response_model=RadiologyAppointmentResponse,
    status_code=201
)
def create_radiology_appointment(

    radiology_registration_id: int = Form(
        ...
    ),

    lab_test_id: int = Form(
        ...
    ),

    appointment_date: date = Form(
        ...
    ),

    appointment_time: time = Form(
        ...
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyAppointmentService(
        db
    )

    return service.create_appointment(

        radiology_registration_id=(
            radiology_registration_id
        ),

        lab_test_id=lab_test_id,

        appointment_date=(
            appointment_date
        ),

        appointment_time=(
            appointment_time
        ),

        remarks=remarks,
    )


# ========================================
# GET ALL APPOINTMENTS
# ========================================
@router.get(
    "/",
    response_model=list[
        RadiologyAppointmentResponse
    ]
)
def get_all_radiology_appointments(

    db: Session = Depends(get_db)
):

    service = RadiologyAppointmentService(
        db
    )

    return service.get_all_appointments()


# ========================================
# GET APPOINTMENT BY ID
# ========================================
@router.get(
    "/{appointment_id}",
    response_model=RadiologyAppointmentResponse
)
def get_radiology_appointment(

    appointment_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyAppointmentService(
        db
    )

    return service.get_appointment(
        appointment_id
    )

# ========================================
# UPDATE APPOINTMENT
# ========================================
@router.put(
    "/{appointment_id}",
    response_model=RadiologyAppointmentResponse
)
def update_radiology_appointment(

    appointment_id: int,

    appointment_date: date | None = Form(
        default=None
    ),

    appointment_time: time | None = Form(
        default=None
    ),

    status: str | None = Form(
        default=None
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyAppointmentService(
        db
    )

    return service.update_appointment(

        appointment_id=appointment_id,

        appointment_date=(
            appointment_date
        ),

        appointment_time=(
            appointment_time
        ),

        status=status,

        remarks=remarks,
    )

# ========================================
# DELETE APPOINTMENT
# ========================================
@router.delete(
    "/{appointment_id}"
)
def delete_radiology_appointment(

    appointment_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyAppointmentService(
        db
    )

    return service.delete_appointment(
        appointment_id
    )