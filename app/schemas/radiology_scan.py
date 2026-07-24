from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ========================================
# RESPONSE SCHEMA
# ========================================
class RadiologyScanResponse(BaseModel):

    id: int

    appointment_id: int

    status: str

    technician_name: Optional[str] = None

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    remarks: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )