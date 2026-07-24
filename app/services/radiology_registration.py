from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_registration import (
    RadiologyRegistration
)


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
        remarks: str | None,
    ):

        # --------------------------------
        # Patient validation
        # --------------------------------

        # Either patient_id or external_id
        # must be provided
        if patient_id is None and external_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Either patient_id or external_id "
                    "must be provided."
                )
            )

        # Both should not be provided together
        if patient_id is not None and external_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Provide either patient_id or external_id, "
                    "not both."
                )
            )

        # --------------------------------
        # Create Registration
        # --------------------------------
        registration = RadiologyRegistration(
            patient_id=patient_id,
            external_id=external_id,
            test_name=test_name,
            test_category=test_category,
            doctor_name=doctor_name,
            status="Registered",
            remarks=remarks,
        )

        self.db.add(registration)

        self.db.commit()

        self.db.refresh(registration)

        return registration

    # --------------------------------
    # Get All Registrations
    # --------------------------------
    def get_all_registrations(self):

        return (
            self.db.query(
                RadiologyRegistration
            )
            .order_by(
                RadiologyRegistration.id.desc()
            )
            .all()
        )

    # --------------------------------
    # Get Registration By ID
    # --------------------------------
    def get_registration(
        self,
        registration_id: int
    ):

        registration = (
            self.db.query(
                RadiologyRegistration
            )
            .filter(
                RadiologyRegistration.id
                == registration_id
            )
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
        remarks: str | None,
    ):

        registration = self.get_registration(
            registration_id
        )

        if test_name is not None:
            registration.test_name = test_name

        if test_category is not None:
            registration.test_category = test_category

        if doctor_name is not None:
            registration.doctor_name = doctor_name

        if status is not None:
            registration.status = status

        if remarks is not None:
            registration.remarks = remarks

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

        registration = self.get_registration(
            registration_id
        )

        self.db.delete(registration)

        self.db.commit()

        return {
            "message": (
                "Radiology registration "
                "deleted successfully."
            )
        }