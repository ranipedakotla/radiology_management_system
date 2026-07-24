from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_appointment import (
    RadiologyAppointment
)

from app.models.radiology_registration import (
    RadiologyRegistration
)

from app.models.lab_tests import LabTest


class RadiologyAppointmentService:

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # CREATE APPOINTMENT
    # ========================================
    def create_appointment(
        self,
        radiology_registration_id: int,
        lab_test_id: int,
        appointment_date,
        appointment_time,
        remarks: str | None,
    ):

        # ------------------------------------
        # Check Radiology Registration
        # ------------------------------------
        registration = (
            self.db.query(
                RadiologyRegistration
            )
            .filter(
                RadiologyRegistration.id
                == radiology_registration_id
            )
            .first()
        )

        if not registration:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Radiology registration "
                    "not found."
                )
            )

        # ------------------------------------
        # Check Lab Test
        # ------------------------------------
        lab_test = (
            self.db.query(
                LabTest
            )
            .filter(
                LabTest.id == lab_test_id
            )
            .first()
        )

        if not lab_test:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab Test not found."
            )

        # ------------------------------------
        # Check Test Availability
        # ------------------------------------
        if not lab_test.is_active:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Selected Lab Test "
                    "is currently unavailable."
                )
            )

        # ------------------------------------
        # Create Appointment
        # ------------------------------------
        appointment = RadiologyAppointment(

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

            status="Scheduled",

            remarks=remarks,
        )

        self.db.add(appointment)

        self.db.commit()

        self.db.refresh(appointment)

        return appointment

    # ========================================
    # GET ALL APPOINTMENTS
    # ========================================
    def get_all_appointments(self):

        return (
            self.db.query(
                RadiologyAppointment
            )
            .order_by(
                RadiologyAppointment.id.desc()
            )
            .all()
        )

    # ========================================
    # GET APPOINTMENT BY ID
    # ========================================
    def get_appointment(
        self,
        appointment_id: int
    ):

        appointment = (
            self.db.query(
                RadiologyAppointment
            )
            .filter(
                RadiologyAppointment.id
                == appointment_id
            )
            .first()
        )

        if not appointment:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Radiology appointment "
                    "not found."
                )
            )

        return appointment

    # ========================================
    # UPDATE APPOINTMENT
    # ========================================
    def update_appointment(
        self,
        appointment_id: int,
        appointment_date,
        appointment_time,
        status: str | None,
        remarks: str | None,
    ):

        appointment = self.get_appointment(
            appointment_id
        )

        # Update appointment date
        if appointment_date is not None:

            appointment.appointment_date = (
                appointment_date
            )

        # Update appointment time
        if appointment_time is not None:

            appointment.appointment_time = (
                appointment_time
            )

        # Update status
        if status is not None:

            appointment.status = status

        # Update remarks
        if remarks is not None:

            appointment.remarks = remarks

        self.db.commit()

        self.db.refresh(appointment)

        return appointment

    # ========================================
    # DELETE / CANCEL APPOINTMENT
    # ========================================
    def delete_appointment(
        self,
        appointment_id: int
    ):

        appointment = self.get_appointment(
            appointment_id
        )

        self.db.delete(appointment)

        self.db.commit()

        return {
            "message": (
                "Radiology appointment "
                "deleted successfully."
            )
        }