

from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime

# ---------- INBOUND ----------
class AdmitIn(BaseModel):
    patient_id: int
    doctor_id: int
    bed_id: int | None = None
    bed_code: str | None = None
    admit_datetime: datetime | None = None
    reason: str | None = None

class TransferIn(BaseModel):
    to_bed_id: int | None = None
    to_bed_code: str | None = None
    transfer_datetime: datetime | None = None
    notes: str | None = None

class DischargeIn(BaseModel):
    discharge_datetime: datetime | None = None
    outcome: str | None = None
    summary: str | None = None
    advice: str | None = None
    created_by_user_id: int | None = None

# ---------- OUTBOUND ----------
class AdmissionOut(BaseModel):
    id: int
    admission_no: str
    status: str
    admit_datetime: datetime
    reason: str | None = None
    patient_name: str
    doctor_name: str
    bed_id: int
    bed_code: str
    bed_group: str | None = None
    floor: str | None = None
    class Config:
        from_attributes = True

class AdmissionListItem(BaseModel):
    id: int
    admission_no: str
    status: str
    admit_datetime: datetime
    patient_name: str
    doctor_name: str
    bed_code: str
    class Config:
        from_attributes = True

class AdmissionListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdmissionListItem]
