from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.people import Patient
from app.models.radiology_patient import RadiologyPatient
from app.models.radiology_registration import RadiologyRegistration


class RadiologyRegistrationService:

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------
    # Create Registration
    # --------------------------------
    def create_registration(
        self,
        patient_id: int | None,
        external_id: int | None,
        test_name: str,
        test_category: str | None,
        doctor_name: str | None,

    ):

        if patient_id is None and external_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either patient_id or external_id must be provided."
            )

        if patient_id is not None and external_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either patient_id or external_id, not both."
            )

        # ------------------------------
        # Validate HMS Patient
        # ------------------------------
        if patient_id is not None:

            patient = (
                self.db.query(Patient)
                .filter(Patient.id == patient_id)
                .first()
            )

            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="HMS patient not found."
                )

        # ------------------------------
        # Validate Radiology Patient
        # ------------------------------
        if external_id is not None:

            radiology_patient = (
                self.db.query(RadiologyPatient)
                .filter(RadiologyPatient.id == external_id)
                .first()
            )

            if not radiology_patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Radiology patient not found."
                )

        # ------------------------------
        # Create Registration
        # ------------------------------
        registration = RadiologyRegistration(
            patient_id=patient_id,
            external_id=external_id,
            test_name=test_name,
            test_category=test_category,
            doctor_name=doctor_name,
            status="Booked",
            scan_status="Pending",
        )

        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)

        # ------------------------------
        # Generate Registration ID
        # ------------------------------
        registration.registration_id = f"RAD{registration.id:06d}"

        self.db.commit()
        self.db.refresh(registration)

        return registration

    # --------------------------------
    # Get All Registrations
    # --------------------------------
    def get_all_registrations(self):

        return (
            self.db.query(RadiologyRegistration)
            .order_by(RadiologyRegistration.id.desc())
            .all()
        )

    # --------------------------------
    # Get Registration
    # --------------------------------
    def get_registration(
        self,
        registration_id: int
    ):

        registration = (
            self.db.query(RadiologyRegistration)
            .filter(RadiologyRegistration.id == registration_id)
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology registration not found."
            )

        return registration

    # --------------------------------
    # Update Registration
    # --------------------------------
    def update_registration(
        self,
        registration_id: int,
        test_name: str | None,
        test_category: str | None,
        doctor_name: str | None,
        status: str | None,
        scan_status: str | None,
    ):

        registration = self.get_registration(registration_id)

        if test_name is not None:
            registration.test_name = test_name

        if test_category is not None:
            registration.test_category = test_category

        if doctor_name is not None:
            registration.doctor_name = doctor_name

        if status is not None:
            registration.status = status

        if scan_status is not None:
            registration.scan_status = scan_status

        self.db.commit()
        self.db.refresh(registration)

        return registration

    # --------------------------------
    # Delete Registration
    # --------------------------------
    def delete_registration(
        self,
        registration_id: int
    ):

        registration = self.get_registration(registration_id)

        self.db.delete(registration)
        self.db.commit()

        return {
            "message": "Radiology registration deleted successfully."
        }