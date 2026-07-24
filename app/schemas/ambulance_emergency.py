from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import enum


# ================== ENUMS ==================

class EmergencyType(str, enum.Enum):
    ACCIDENT = "ACCIDENT"
    CARDIAC = "CARDIAC"
    TRAUMA = "TRAUMA"


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    START_PICKUP = "START_PICKUP"
    PICKED_UP = "PICKED_UP"
    TRANSPORTING = "TRANSPORTING"
    DROPPED = "DROPPED"
    COMPLETED = "COMPLETED"


# ================== BASE ==================

class EmergencyRequestBase(BaseModel):
    patient_name: str

    contact: str = Field(..., min_length=10, max_length=15)

    pickup_location: str
    drop_location: Optional[str] = None

    latitude: float
    longitude: float

    emergency_type: Optional[EmergencyType] = None

    hospital_id: Optional[int] = None

    ambulance_id: int


# ================== CREATE ==================

class EmergencyRequestCreate(EmergencyRequestBase):
    pass


# ================== UPDATE ==================

class EmergencyRequestUpdate(BaseModel):
    patient_name: Optional[str]
    contact: Optional[str]

    pickup_location: Optional[str]
    drop_location: Optional[str]

    latitude: Optional[float]
    longitude: Optional[float]

    emergency_type: Optional[EmergencyType]
    status: Optional[RequestStatus]

    hospital_id: Optional[int]
    ambulance_id: Optional[int]


# ================== RESPONSE ==================

class EmergencyRequestResponse(EmergencyRequestBase):
    id: int
    status: RequestStatus
    created_at: datetime

    class Config:
        from_attributes = True