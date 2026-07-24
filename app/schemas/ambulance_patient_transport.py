from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum


# ================== ENUMS ==================

class PatientCondition(str, enum.Enum):
    STABLE = "STABLE"
    CRITICAL = "CRITICAL"


class ReferredBy(str, enum.Enum):
    HOSPITAL = "HOSPITAL"
    POLICE = "POLICE"
    PUBLIC = "PUBLIC"


# ================== BASE ==================

class PatientTransportBase(BaseModel):
    request_id: int

    # Patient Info
    patient_name: str
    age: int
    gender: str

    primary_contact: str
    secondary_contact: Optional[str]

    # Locations
    pickup_location: str
    drop_location: str

    # Medical
    condition_at_pickup: Optional[PatientCondition]
    referred_by: Optional[ReferredBy]

    attendant_name: Optional[str]


# ================== CREATE ==================

class PatientTransportCreate(PatientTransportBase):
    pass


# ================== UPDATE ==================

class PatientTransportUpdate(BaseModel):
    patient_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]

    primary_contact: Optional[str]
    secondary_contact: Optional[str]

    pickup_location: Optional[str]
    drop_location: Optional[str]

    condition_at_pickup: Optional[PatientCondition]
    referred_by: Optional[ReferredBy]

    attendant_name: Optional[str]


# ================== RESPONSE ==================

class PatientTransportResponse(PatientTransportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TripResponse(BaseModel):
    id: int
    request_id: int
    ambulance_id: int
    hospital_id: int
    start_time: datetime
    end_time: Optional[datetime]
    distance_km: float

    class Config:
        orm_mode = True