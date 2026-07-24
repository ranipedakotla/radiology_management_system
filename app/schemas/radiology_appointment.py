from datetime import date, time, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ========================================
# CREATE APPOINTMENT
# ========================================
class RadiologyAppointmentCreate(BaseModel):

    # Existing radiology registration ID
    radiology_registration_id: int

    # Selected test ID from lab_tests
    lab_test_id: int

    # Appointment date
    appointment_date: date

    # Appointment time
    appointment_time: time

    # Optional remarks
    remarks: Optional[str] = None


# ========================================
# UPDATE APPOINTMENT
# ========================================
class RadiologyAppointmentUpdate(BaseModel):

    appointment_date: Optional[date] = None

    appointment_time: Optional[time] = None

    status: Optional[str] = None

    remarks: Optional[str] = None


# ========================================
# APPOINTMENT RESPONSE
# ========================================
class RadiologyAppointmentResponse(BaseModel):

    id: int

    radiology_registration_id: int

    lab_test_id: int

    appointment_date: date

    appointment_time: time

    status: str

    remarks: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )