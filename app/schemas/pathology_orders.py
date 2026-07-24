from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ---- Create Order ----
class OrderCreateIn(BaseModel):
    patient_id: int
    doctor_id: Optional[int] = None
    priority: str = "normal"
    source: Optional[str] = "walk-in"
    tests: List[int] = Field(default_factory=list)
    panels: List[int] = Field(default_factory=list)


class OrderItemOut(BaseModel):
    id: int
    test_id: int
    panel_id: int | None
    sample_id: int | None
    status: str


# class OrderOut(BaseModel):
#     id: int
#     order_no: str | None
#     patient_id: int
#     doctor_id: int | None
#     priority: str
#     source: str | None
#     status: str
#     items: List[OrderItemOut]


# ---- Accession ----
class AccessionIn(BaseModel):
    remarks: Optional[str] = None
    sample_collected_at: Optional[datetime] = None  # NEW
    sample_type_id: Optional[int] = None


# ---- Results Entry ----
class ResultValueIn(BaseModel):
    analyte_id: int
    value_text: Optional[str] = None
    value_num: Optional[float] = None
    interpretation: Optional[str] = None   # NEW
    note: Optional[str] = None

class ResultEntryValueIn(BaseModel):
    analyte_id: int
    value_num: Optional[float] = None
    value_text: Optional[str] = None
    interpretation: Optional[str] = None   # NEW
    note: Optional[str] = None

class ResultEntryIn(BaseModel):
    order_item_id: int
    test_interpretation: Optional[str] = None
    test_note: Optional[str] = None
    values: List[ResultValueIn]

class ResultsBatchIn(BaseModel):
    entries: List[ResultEntryIn]


# ---- Validation ----
class ValidationIn(BaseModel):
    comments: Optional[str] = None

class ReportOut(BaseModel):
    id: int
    version: int
    is_current: bool
    pdf_url: Optional[str] = None  # include pdf_url

    class Config:
        orm_mode = True

class OrderOut(BaseModel):
    id: int
    order_no: Optional[str] = None
    patient_id: int
    doctor_id: Optional[int] = None
    priority: str
    source: Optional[str] = None
    status: str
    items: List[OrderItemOut]
    reports: List[ReportOut] = []  # ✅ add reports here

    class Config:
        orm_mode = True
