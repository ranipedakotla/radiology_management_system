from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class Vitals(BaseModel):
    height_cm: int | None = None
    weight_kg: float | None = None
    temp_c: float | None = None
    bp_systolic: int | None = None
    bp_diastolic: int | None = None
    blood_sugar_bf: float | None = None
    blood_sugar_af: float | None = None
    pulse: int | None = None
    resp_rate: int | None = None
    spo2: int | None = None

class DiagnosisIn(BaseModel):
    icd_code: str | None = None
    description: str
    is_primary: bool = False

class PrescriptionItemIn(BaseModel):
    drug_name: str
    dose: str | None = None
    frequency: str | None = None
    duration: str | None = None
    route: str | None = None
    instructions: str | None = None
    quantity: int | None = None
    unit: str | None = None

Priority = Literal["Routine", "Urgent", "Stat"]

class LabTestIn(BaseModel):
    test_name: str
    test_code: str | None = None
    priority: Priority = "Routine"
    notes: str | None = None

class LabTestOut(BaseModel):
    id: int
    test_name: str
    test_code: str | None = None
    priority: Priority
    notes: str | None = None
    status: str

class VisitCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: int
    visit_date: datetime
    ward_name: str | None = None
    chief_complaint: str | None = None
    # blood_sugar_bf: float
    # blood_sugar_af: float
    symptoms: str | None = None
    notes: str | None = None
    vitals: Vitals | None = None
    diagnoses: list[DiagnosisIn] = []
    prescription_items: list[PrescriptionItemIn] = []
    lab_tests: list[LabTestIn] = []  # include in create

class VisitOutIDs(BaseModel):
    id: int
    visit_id: str
    patient_id: int
    doctor_id: int
    # ward_name: str
    chief_complaint: str | None = None
    appointment_id: int | None = None
    blood_sugar_bf: float | None = None
    blood_sugar_af: float | None = None
    visit_date: datetime

    class Config:
        from_attributes = True

class VisitListItem(BaseModel):
    id: int
    visit_id: str
    appointment_id:int | None = None
    patient_name: str
    doctor_name: str
    department: str
    visit_date: datetime
    patient_id: int
    doctor_id: int
    age: int | None = None
    gender: str | None = None
    phone_number: str | None = None
    chief_complaint: str | None = None
    class Config:
        from_attributes = True

class VisitDetail(VisitListItem):
    symptoms: str | None = None
    notes: str | None = None
    vitals: Vitals | None = None
    diagnoses: list[DiagnosisIn] = []
    prescription: list[PrescriptionItemIn] = []
    lab_tests: list[LabTestOut] = []  # returned by service

class VisitListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[VisitListItem]
