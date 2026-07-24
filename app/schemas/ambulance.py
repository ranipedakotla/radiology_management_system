from datetime import datetime

from pydantic import BaseModel
from typing import Optional
import enum

from app.models.ambulance import BookingType, EmergencyType, PaymentMode


# ================== ENUMS ==================

class AmbulanceStatus(str, enum.Enum):
    OFFLINE = "OFFLINE"
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    INACTIVE = "INACTIVE"


class AmbulanceType(str, enum.Enum):
    BLS = "BLS"
    ALS = "ALS"
    CARDIAC_AMBULANCE = "CARDIAC_AMBULANCE"
    NICA_AMBULANCE = "NICA_AMBULANCE"
    PATIENT_TRANSPORT_VEHICLE = "PATIENT_TRANSPORT_VEHICLE"
    DEAD_BODY_FREEZER_AMBULANCE = "DEAD_BODY_FREEZER_AMBULANCE"


# ================== BASE ==================

class AmbulanceBase(BaseModel):
    registration_number: str
    ambulance_type: Optional[AmbulanceType]
    status: Optional[AmbulanceStatus] = AmbulanceStatus.OFFLINE
    latitude: Optional[float]
    longitude: Optional[float]
    # crew_id: Optional[int]


# ================== CREATE ==================

class AmbulanceCreate(AmbulanceBase):
    registration_number: str   # required


# ================== UPDATE ==================

class AmbulanceUpdate(BaseModel):
    ambulance_type: Optional[AmbulanceType]
    status: Optional[AmbulanceStatus]
    latitude: Optional[float]
    longitude: Optional[float]
    # crew_id: Optional[int]


# ================== RESPONSE ==================

class AmbulanceResponse(AmbulanceBase):
    id: int

    class Config:
        from_attributes = True   # for SQLAlchemy (Pydantic v2)


# -------------------------
# Create Booking
# -------------------------
class BookingCreate(BaseModel):
    booking_type: BookingType

    caller_name: str
    caller_phone: str

    pickup_location: str
    drop_location: str

    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None

    emergency_type: EmergencyType
    payment_mode: PaymentMode


# -------------------------
# Update Booking
# -------------------------
class BookingUpdate(BaseModel):
    booking_type: Optional[BookingType] = None

    caller_name: Optional[str] = None
    caller_phone: Optional[str] = None

    pickup_location: Optional[str] = None
    drop_location: Optional[str] = None

    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None

    emergency_type: Optional[EmergencyType] = None
    payment_mode: Optional[PaymentMode] = None


# -------------------------
# Response Schema
# -------------------------
class BookingResponse(BaseModel):
    id: int
    booking_id: str

    booking_datetime: datetime
    booking_type: BookingType

    caller_name: str
    caller_phone: str

    pickup_location: str
    drop_location: str

    patient_name: Optional[str]
    patient_age: Optional[int]
    patient_gender: Optional[str]

    emergency_type: EmergencyType
    payment_mode: PaymentMode

    created_at: datetime

    class Config:
        from_attributes = True   # Pydantic v2