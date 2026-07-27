from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --------------------------------
# Create Refund
# --------------------------------
class RefundCreate(BaseModel):

    registration_id: int

    refund_amount: float

    refund_reason: str

    remarks: Optional[str] = None


# --------------------------------
# Update Refund
# --------------------------------
class RefundUpdate(BaseModel):

    refund_amount: Optional[float] = None

    refund_reason: Optional[str] = None

    status: Optional[str] = None

    remarks: Optional[str] = None


# --------------------------------
# Response Schema
# --------------------------------
class RefundResponse(BaseModel):

    id: int

    registration_id: int

    refund_amount: float

    refund_reason: str

    status: str

    remarks: Optional[str] = None

    created_at: datetime

    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )