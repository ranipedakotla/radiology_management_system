from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum


# ================== ENUM ==================

class PaymentMode(str, enum.Enum):
    CASH = "CASH"
    CASHLESS = "CASHLESS"


# ==================  RESOURCE USAGE ==================

class ResourceUsageBase(BaseModel):
    request_id: int

    oxygen_start_time: Optional[datetime]
    oxygen_end_time: Optional[datetime]

    ventilator_minutes: Optional[int]

    ecg_used: Optional[bool] = False
    suction_used: Optional[bool] = False
    defibrillator_used: Optional[bool] = False

    emergency_medicines_qty: Optional[int]
    iv_fluids_qty: Optional[int]


class ResourceUsageCreate(ResourceUsageBase):
    pass


class ResourceUsageUpdate(BaseModel):
    oxygen_start_time: Optional[datetime]
    oxygen_end_time: Optional[datetime]
    ventilator_minutes: Optional[int]

    ecg_used: Optional[bool]
    suction_used: Optional[bool]
    defibrillator_used: Optional[bool]

    emergency_medicines_qty: Optional[int]
    iv_fluids_qty: Optional[int]


class ResourceUsageResponse(ResourceUsageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================  BILLING ==================

class BillingBase(BaseModel):
    request_id: int

    base_charge: Optional[float]
    distance_km: Optional[float]
    distance_charge: Optional[float]

    oxygen_charge: Optional[float]
    ventilator_charge: Optional[float]
    device_charge: Optional[float]

    waiting_charge: Optional[float]
    night_charge: Optional[float]

    gst_amount: Optional[float]
    total_amount: Optional[float]


class BillingCreate(BillingBase):
    pass


class BillingUpdate(BaseModel):
    base_charge: Optional[float]
    distance_km: Optional[float]
    distance_charge: Optional[float]

    oxygen_charge: Optional[float]
    ventilator_charge: Optional[float]
    device_charge: Optional[float]

    waiting_charge: Optional[float]
    night_charge: Optional[float]

    gst_amount: Optional[float]
    total_amount: Optional[float]


class BillingResponse(BillingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================  INSURANCE ==================

class InsuranceBase(BaseModel):
    billing_id: int
    payment_mode: Optional[PaymentMode]

    insurance_covered_amount: Optional[float]
    patient_payable_amount: Optional[float]


class InsuranceCreate(InsuranceBase):
    pass


class InsuranceUpdate(BaseModel):
    payment_mode: Optional[PaymentMode]
    insurance_covered_amount: Optional[float]
    patient_payable_amount: Optional[float]


class InsuranceResponse(BaseModel):
    id: int
    billing_id: int
    payment_mode: str
    insurance_covered_amount: float
    patient_payable_amount: float

    class Config:
        from_attributes = True