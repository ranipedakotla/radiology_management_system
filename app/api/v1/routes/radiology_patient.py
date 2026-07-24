from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_patient import (
    RadiologyPatientCreate,
    RadiologyPatientUpdate,
    RadiologyPatientResponse,
)

from app.services.radiology_patient import (
    RadiologyPatientService,
)


router = APIRouter(
    prefix="/radiology-patients",
    tags=["Radiology Patients"]
)


# ---------------------------------
# Create Radiology Patient
# ---------------------------------
@router.post(
    "/",
    response_model=RadiologyPatientResponse,
    status_code=201
)
def create_radiology_patient(
    patient: RadiologyPatientCreate,
    db: Session = Depends(get_db)
):

    service = RadiologyPatientService(db)

    return service.create_patient(patient)


# ---------------------------------
# Get All Radiology Patients
# ---------------------------------
@router.get(
    "/",
    response_model=list[RadiologyPatientResponse]
)
def get_all_radiology_patients(
    db: Session = Depends(get_db)
):

    service = RadiologyPatientService(db)

    return service.get_all_patients()


# ---------------------------------
# Get Radiology Patient By ID
# ---------------------------------
@router.get(
    "/{patient_id}",
    response_model=RadiologyPatientResponse
)
def get_radiology_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):

    service = RadiologyPatientService(db)

    return service.get_patient(patient_id)


# ---------------------------------
# Update Radiology Patient
# ---------------------------------
@router.put(
    "/{patient_id}",
    response_model=RadiologyPatientResponse
)
def update_radiology_patient(
    patient_id: int,
    patient: RadiologyPatientUpdate,
    db: Session = Depends(get_db)
):

    service = RadiologyPatientService(db)

    return service.update_patient(
        patient_id,
        patient
    )


# ---------------------------------
# Delete Radiology Patient
# ---------------------------------
@router.delete(
    "/{patient_id}"
)
def delete_radiology_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):

    service = RadiologyPatientService(db)

    return service.delete_patient(patient_id)