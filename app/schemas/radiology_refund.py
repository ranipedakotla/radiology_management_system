from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RefundResponse(BaseModel):

    id: int

    registration_id: int

    cancellation_reason: str

    refund_amount: float

    approval_status: str

    refund_mode: Optional[str] = None

    refund_status: str

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )