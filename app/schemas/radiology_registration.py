from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

# --------------------------------
# Response Schema
# --------------------------------
class RadiologyRegistrationResponse(BaseModel):

    id: int

    patient_id: Optional[int] = None

    external_id: Optional[int] = None

    test_name: str

    test_category: Optional[str] = None

    doctor_name: Optional[str] = None

    status: str

    remarks: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )
