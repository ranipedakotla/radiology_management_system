from __future__ import annotations

from datetime import date

from pydantic import BaseModel

class DoctorCountOut(BaseModel):
    total_doctors: int

class PatientCountOut(BaseModel):
    total_patients: int

class DoctorLiteOut(BaseModel):
    id: int
    name: str
    consultation_fee: int | None = None
    specialty:str

class PatientLiteOut(BaseModel):
    id: int
    name: str
    phone_number: str | None = None
    gender: str | None = None
    dob: date | None = None



