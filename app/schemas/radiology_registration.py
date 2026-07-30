from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RadiologyRegistrationResponse(BaseModel):

    id: int

    # Registration ID
    registration_id: Optional[str] = None

    # Existing HMS Patient
    patient_id: Optional[int] = None

    # Manual Radiology Patient
    external_id: Optional[int] = None

    # Test Details
    test_name: str

    test_category: Optional[str] = None

    doctor_name: Optional[str] = None

    # Registration Status
    status: str

    # Scan Status
    scan_status: str

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )
