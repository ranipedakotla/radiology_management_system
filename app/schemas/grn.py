# schemas/grn.py

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime
class GRNItemCreate(BaseModel):
    medicine_id: int
    ordered_qty: int = Field(..., gt=0)
    received_qty: int = Field(..., gt=0)
    damaged_qty: int = Field(0, ge=0)

    batch_number: str
    expiry_date: datetime

class GRNCreate(BaseModel):
        vendor_id: int
        po_id: str

        invoice_number: str
        received_by: str
        remarks: Optional[str] = None

        items: List[GRNItemCreate]

class GRNItemOut(GRNItemCreate):
        id: int
        model_config = ConfigDict(from_attributes=True)

class GRNOut(BaseModel):
        id: int
        grn_number: str
        vendor_id: int
        po_id: str
        received_date: datetime

        items: List[GRNItemOut]

        model_config = ConfigDict(from_attributes=True)