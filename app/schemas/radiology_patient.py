from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


# ---------------------------------
# Create Radiology Patient
# ---------------------------------
class RadiologyPatientCreate(BaseModel):

    first_name: str

    last_name: Optional[str] = None

    dob: Optional[date] = None

    phone_number: str

    guardian_name: Optional[str] = None

    gender: Optional[str] = None

    age: Optional[int] = None

    marital_status: Optional[str] = None

    email: Optional[EmailStr] = None

    location: Optional[str] = None

    diagnosis: Optional[str] = None

    reason: Optional[str] = None

    aadhaar_no: Optional[str] = None

    aadhaar_file_path: Optional[str] = None


# ---------------------------------
# Update Radiology Patient
# ---------------------------------
class RadiologyPatientUpdate(BaseModel):

    first_name: Optional[str] = None

    last_name: Optional[str] = None

    dob: Optional[date] = None

    phone_number: Optional[str] = None

    guardian_name: Optional[str] = None

    gender: Optional[str] = None

    age: Optional[int] = None

    marital_status: Optional[str] = None

    email: Optional[EmailStr] = None

    location: Optional[str] = None

    diagnosis: Optional[str] = None

    reason: Optional[str] = None

    aadhaar_no: Optional[str] = None

    aadhaar_file_path: Optional[str] = None


# ---------------------------------
# Response Schema
# ---------------------------------
class RadiologyPatientResponse(BaseModel):

    id: int

    first_name: str

    last_name: Optional[str]

    dob: Optional[date]

    phone_number: str

    guardian_name: Optional[str]

    gender: Optional[str]

    age: Optional[int]

    marital_status: Optional[str]

    email: Optional[EmailStr]

    location: Optional[str]

    diagnosis: Optional[str]

    reason: Optional[str]

    aadhaar_no: Optional[str]

    aadhaar_file_path: Optional[str]

    created_at: datetime

    updated_at: Optional[datetime]

    model_config = ConfigDict(
        from_attributes=True
    )