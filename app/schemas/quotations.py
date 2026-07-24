from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date



class QuotationItemCreate(BaseModel):
    medicine_name: str
    dosage: str
    quantity: int
    mrp: float
    price: float
    cgst: float
    sgst: float
    discount_price: float = 0
    final_price: float
model_config = ConfigDict(from_attributes=True)

class QuotationCreate(BaseModel):
    vendor_id: int
    vendor_name: str
    drug_license_no: str
    gst_no: str
    place_of_supply: str
    quotation_date: date
    invoice_no: Optional[str] = None
    items: List[QuotationItemCreate]



class QuotationUpdate(BaseModel):
    vendor_name: Optional[str] = None
    drug_license_no: Optional[str] = None
    gst_no: Optional[str] = None
    place_of_supply: Optional[str] = None
    invoice_no: Optional[str] = None
    quotation_date: Optional[date] = None
    is_approved: Optional[bool] = None


class QuotationItemResponse(QuotationItemCreate):
    total_price: float
    final_price: float

    class Config:
        from_attributes = True


class QuotationResponse(BaseModel):
    id: int
    vendor_name: str
    gst_no: str
    total_amount: float
    total_discount: float
    net_amount: float
    items: List[QuotationItemResponse]

    class Config:
        from_attributes = True

class QuotationItemOut(BaseModel):
    medicine_name: str
    dosage: str
    quantity: int
    mrp: float
    price: float
    cgst: float
    sgst: float
    total_price: float
    discount_price: float
    final_price: float

    class Config:
        from_attributes = True


class QuotationOut(BaseModel):
    id: int
    vendor_name: str
    drug_license_no: str
    gst_no: str
    place_of_supply: str
    quotation_date: date
    invoice_no: str
    total_amount: float
    total_discount: float
    net_amount: float
    is_approved: bool
    items: List[QuotationItemOut]

    model_config = ConfigDict(from_attributes=True)
