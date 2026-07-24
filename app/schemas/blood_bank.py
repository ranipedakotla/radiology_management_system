from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
from enum import Enum as PyEnum

# ===================== ENUM SCHEMAS =====================

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    LAB_TECH = "LAB_TECH"
    BLOOD_BANK_STAFF = "BLOOD_BANK_STAFF"
    DOCTOR = "DOCTOR"
    RECEPTIONIST = "RECEPTIONIST"


class TestStatus(str, PyEnum):
    PENDING = "PENDING"
    TESTED = "TESTED"
    AVAILABLE = "AVAILABLE"
    REJECTED = "REJECTED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"


class BloodStatus(str, Enum):
    PENDING_LAB = "PENDING_LAB"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class RequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    ISSUED = "ISSUED"
    REJECTED = "REJECTED"
    MATCHED = "MATCHED"
    COMPLETED = "COMPLETED"


class ComponentType(str, Enum):
    RBC = "RBC"
    PLASMA = "PLASMA"
    PLATELETS = "PLATELETS"


# ===================== USER SCHEMAS =====================

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ===================== DONOR SCHEMAS =====================

class DonorBase(BaseModel):
    first_name: str
    email: EmailStr
    phone: str
    address: str
    blood_group: str
    gender: Optional[str]
    age: int
    last_donation_date: Optional[date] = None
    wants_exchange: bool = False
    exchange_blood_group: str | None =  None


class DonorCreate(DonorBase):
    pass


class DonorResponse(DonorBase):
    id: int
    eligibility: Optional[str] = None
    eligibility_checked_at: Optional[datetime] = None
    eligibility_checked_by: Optional[int] = None  # doctor ID

    class Config:
        from_attributes = True


# ===================== BLOOD COLLECTION =====================

class BloodCollectionCreate(BaseModel):
    donor_id: int
    collection_date: Optional[date] = None


class BloodCollectionResponse(BaseModel):
    id: int
    donor_id: int
    collection_date: date
    test_status: TestStatus
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ===================== BLOOD INVENTORY =====================

class BloodInventoryLabUpdate(BaseModel):
    quantity_ml: int
    storage_rack: str

class BloodInventoryCreate(BaseModel):

    collection_id:int
    blood_group:str
    component_type:ComponentType
    storage_rack:Optional[str]
    expiry_date: date
    status:BloodStatus

class BloodInventoryResponse(BaseModel):
    id: int
    collection_id: int
    blood_group: str
    component_type: ComponentType
    storage_rack: Optional[str]
    quantity_ml: Optional[int]
    expiry_date: date
    status: BloodStatus
    is_expired: bool

    class Config:
        from_attributes = True


# ===================== BLOOD TEST REPORT =====================

class BloodTestReportCreate(BaseModel):
    collection_id: int
    hiv: bool
    hbv: bool
    hcv: bool
    malaria: bool
    syphilis: bool
    eligibility: bool
    test_date: Optional[datetime] = None


class BloodTestReportResponse(BloodTestReportCreate):
    id: int
    eligibility: bool
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True


# ===================== PATIENT SCHEMAS =====================

class PatientBase(BaseModel):
    name: str
    age: Optional[int]
    phone: Optional[str]
    address: Optional[str]
    gender: Optional[str]
    blood_group: Optional[str]
    diagnosis: Optional[str]


class PatientCreate(PatientBase):
    pass


class PatientResponse(PatientBase):
    id: int

    class Config:
        from_attributes = True


# ===================== BLOOD REQUEST SCHEMAS =====================

class BloodRequestCreate(BaseModel):
    patient_id: int
    blood_group: str  # Blood patient NEEDS
    exchange_blood_group: Optional[str] = None  # Blood patient CAN GIVE (for exchange)
    component_type: ComponentType
    units_required: int
    allow_exchange: bool = False


class BloodRequestResponse(BaseModel):
    id: int
    patient_id: int
    blood_group: str
    exchange_blood_group: Optional[str] = None
    component_type: ComponentType
    units_required: int
    allow_exchange: bool
    status: RequestStatus
    matched_request_id: Optional[int] = None  # shows exchange partner
    matched_donor_id: Optional[int] = None  # new field for donor-driven exchange

    class Config:
        from_attributes = True
