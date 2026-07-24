from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_patient import RadiologyPatient
from app.schemas.radiology_patient import (
    RadiologyPatientCreate,
    RadiologyPatientUpdate,
)


class RadiologyPatientService:

    def __init__(self, db: Session):
        self.db = db

    # ---------------------------------
    # Create Radiology Patient
    # ---------------------------------
    def create_patient(
        self,
        patient_data: RadiologyPatientCreate
    ):

        new_patient = RadiologyPatient(
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            dob=patient_data.dob,
            phone_number=patient_data.phone_number,
            guardian_name=patient_data.guardian_name,
            gender=patient_data.gender,
            age=patient_data.age,
            marital_status=patient_data.marital_status,
            email=patient_data.email,
            location=patient_data.location,
            diagnosis=patient_data.diagnosis,
            reason=patient_data.reason,
            aadhaar_no=patient_data.aadhaar_no,
            aadhaar_file_path=patient_data.aadhaar_file_path,
        )

        self.db.add(new_patient)

        self.db.commit()

        self.db.refresh(new_patient)

        return new_patient

    # ---------------------------------
    # Get All Radiology Patients
    # ---------------------------------
    def get_all_patients(self):

        return (
            self.db.query(RadiologyPatient)
            .order_by(RadiologyPatient.id.desc())
            .all()
        )

    # ---------------------------------
    # Get Patient By ID
    # ---------------------------------
    def get_patient(
        self,
        patient_id: int
    ):

        patient = (
            self.db.query(RadiologyPatient)
            .filter(
                RadiologyPatient.id == patient_id
            )
            .first()
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology patient not found."
            )

        return patient

    # ---------------------------------
    # Update Radiology Patient
    # ---------------------------------
    def update_patient(
        self,
        patient_id: int,
        patient_data: RadiologyPatientUpdate
    ):

        patient = (
            self.db.query(RadiologyPatient)
            .filter(
                RadiologyPatient.id == patient_id
            )
            .first()
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology patient not found."
            )

        update_data = patient_data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(
                patient,
                field,
                value
            )

        self.db.commit()

        self.db.refresh(patient)

        return patient

    # ---------------------------------
    # Delete Radiology Patient
    # ---------------------------------
    def delete_patient(
        self,
        patient_id: int
    ):

        patient = (
            self.db.query(RadiologyPatient)
            .filter(
                RadiologyPatient.id == patient_id
            )
            .first()
        )

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology patient not found."
            )

        self.db.delete(patient)

        self.db.commit()

        return {
            "message": "Radiology patient deleted successfully."
        }