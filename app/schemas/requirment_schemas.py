from pydantic import BaseModel,ConfigDict
from datetime import date
from typing import Optional

# Medicine
class MedicineBase(BaseModel):
    name: str
    stock: int
    reorder_level: Optional[int] = 10
    fast_moving: Optional[bool] = False
    expiry_date: Optional[date]
    batch_no: Optional[str]
    unit_price: Optional[float]

class MedicineCreate(MedicineBase):
    pass

class MedicineOut(MedicineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Vendor
class VendorBase(BaseModel):
    name: str
    contact: Optional[str]
    email: Optional[str]
    payment_terms: Optional[str]

class VendorCreate(VendorBase):
    pass

class VendorOut(VendorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Quotation
class QuotationBase(BaseModel):
    medicine_id: int
    vendor_id: int
    rate_per_unit: float
    discount_percent: Optional[float] = 0
    gst_percent: Optional[float] = 0
    mrp: float
    available_batch: Optional[str]
    expiry_date: Optional[date]
    delivery_time_days: Optional[int]

class QuotationCreate(QuotationBase):
    pass

class QuotationOut(QuotationBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


