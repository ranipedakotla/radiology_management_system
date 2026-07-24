from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import enum


# ================== ENUMS ==================

class DriverStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class IDProofType(str, enum.Enum):
    AADHAAR = "Aadhaar"
    PASSPORT = "Passport"
    VOTER_ID = "Voter ID"


# ================== BASE ==================

class DriverBase(BaseModel):
    driver_id: str = Field(..., min_length=1)
    driver_name: str

    id_proof_type: IDProofType
    id_proof_number: str

    driver_photo: Optional[str]

    license_number: str
    license_validity_date: date

    primary_phone: str
    secondary_phone: Optional[str]

    address: str

    experience_years: Optional[int] = 0
    active_status: Optional[DriverStatus] = DriverStatus.ACTIVE


# ================== CREATE ==================

class DriverCreate(DriverBase):
    pass


# ================== UPDATE ==================

class DriverUpdate(BaseModel):
    driver_name: Optional[str]

    id_proof_type: Optional[IDProofType]
    id_proof_number: Optional[str]

    driver_photo: Optional[str]

    license_number: Optional[str]
    license_validity_date: Optional[date]

    primary_phone: Optional[str]
    secondary_phone: Optional[str]

    address: Optional[str]

    experience_years: Optional[int]
    active_status: Optional[DriverStatus]


# ================== RESPONSE ==================

class DriverResponse(DriverBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True