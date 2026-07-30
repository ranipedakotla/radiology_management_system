from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --------------------------------
# Response Schema
# --------------------------------
class RadiologyScanResponse(BaseModel):

    id: int

    registration_id: int

    technician_name: Optional[str] = None

    scan_status: str

    hold_reason: Optional[str] = None

    cancellation_reason: Optional[str] = None

    reschedule_date: Optional[datetime] = None

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )