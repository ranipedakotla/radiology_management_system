from pydantic import BaseModel,ConfigDict, Field, field_validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

class MedicineBase(BaseModel):
    hospital_id: int
    branch_id: int
    item_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    company:Optional[str] = None
    hsn_code: Optional[str] = None
    category: str
    strength: str
    dosage_form: str
    price:int

class MedicineCreate(MedicineBase):
        unit_price: float
        quantity: int

        expiry_date: date
        mfg_date: date | None = None
        batch_no: str | None = None

        description: str | None = None
        drug_formula: str | None = None


# class MedicineCreate(MedicineBase):
#     pass
    # model_config = ConfigDict(from_attributes=True)


class MedicineResponse(MedicineBase):
    medicine_id: int
    # hospital_id: int
    # branch_id: int
    batch_number: str
    manufacture_date: date
    expiry_date: date
    vendor_name: str
    quantity_received: int
    mrp: Decimal
    cost_price: Decimal
    gst_percent: Decimal
    cgst: Decimal
    sgst: Decimal
    discount_percent: Decimal
    storage_condition: str

    model_config = ConfigDict(from_attributes=True)

class MedicineRead(MedicineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BatchBase(BaseModel):
    hospital_id: int      
    branch_id: int   
    medicine_id: int
    strength: Optional[str] = None
    batch_number: str
    manufacture_date: date
    expiry_date: date
    vendor_name: str
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    quantity_received: int
    mrp: float
    cost_price: float
    gst_percent: float
    cgst: float
    sgst:float
    discount_percent: float
    rack_shelf_number: Optional[str] = None
    storage_condition: str

class BatchCreate(BatchBase):
    pass

class BatchRead(BatchBase):
    id: int
    quantity_available: int
    total_value: float
    days_until_expiry: int
    model_config = ConfigDict(from_attributes=True)

class StockLedgerBase(BaseModel):
    batch_id: int
    transaction_type: str
    quantity_in: int = 0
    quantity_out: int = 0
    balance_qty: int
    transaction_value: float = 0.0
    remarks: Optional[str] = None

class StockLedgerCreate(StockLedgerBase):
    pass

class StockLedgerRead(StockLedgerBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

#surgical

class SurgicalItemCreate(BaseModel):
    hospital_id: int
    branch_id: int
    item_code: str
    item_name: str
    # price : str
    item_type: str
    size_specification: Optional[str] = None 
    sterility_status: str
    usage_count_per_procedure: int = 1
    unit_of_measure: str


class SurgicalItemRead(SurgicalItemCreate):
    id: int
    # batches: list = []
    model_config = ConfigDict(from_attributes=True)

class SurgicalBatchCreate(BaseModel):
    hospital_id: int
    branch_id: int
    surgical_item_id: Optional[int] = None
    batch_number: str
    manufacture_date: date
    expiry_date: Optional[date] = None
    vendor_name: str
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    quantity_received: int
    mrp: float
    cost_price: float
    gst_percent: float
    cgst: float
    sgst:  float
    discount_percent: float
    sterilization_date: Optional[date] = None
    rack_shelf_number: Optional[str] = None
    storage_condition: str

class SurgicalBatchRead(SurgicalBatchCreate):
    id: int
    quantity_available: int
    total_value: float
    model_config = ConfigDict(from_attributes=True)

class NonSurgicalItemCreate(BaseModel):
    # hospital_id: int
    # branch_id: int
    item_code: str
    item_name: str
    item_type: str
    specification: Optional[str] = None
    usage_per_patient: float = 1.0
    unit_of_measure: str

class NonSurgicalItemRead(NonSurgicalItemCreate):
    id: int
    hospital_id: int
    branch_id: int

    # batches: list = []


class NonSurgicalBatchCreate(BaseModel):
    non_surgical_item_id: int = Field(..., gt=0)
    batch_number: str = Field(..., min_length=1, max_length=50)
    manufacture_date: date
    expiry_date: Optional[date] = Field(None)
    vendor_name: str = Field(..., min_length=1, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=50)
    po_number: Optional[str] = Field(None, max_length=50)
    quantity_received: int = Field(..., gt=0, le=10000)
    mrp: float = Field(..., gt=0, le=100000)
    cost_price: float = Field(..., gt=0, le=100000)
    cgst: float = Field(..., ge=0, le=10000)
    sgst: float = Field(..., ge=0, le=10000)
    gst_percent: float = Field(..., ge=0, le=28)
    discount_percent: float = Field(..., ge=0, le=50)
    rack_shelf_number: Optional[str] = Field(None, max_length=20)
    storage_condition: str = Field(..., min_length=1, max_length=200)

class NonSurgicalBatchRead(NonSurgicalBatchCreate):
    id: int
    quantity_available: int
    total_value: float
    model_config = ConfigDict(from_attributes=True)

# class BatchUpdate(BaseModel):
#     batch_number: Optional[str] = None
#     expiry_date: Optional[date] = None
#     quantity: Optional[int] = None
#     medicine_id: Optional[int] = None
class BatchUpdate(BaseModel):
    medicine_id: int
    batch_number: str
    manufacture_date: date
    expiry_date: date
    quantity: int
    purchase_price: float
    selling_price: float
    supplier_name: str

class MedicineUpdate(BaseModel):
    hospital_id: Optional[int] = None
    branch_id: Optional[int] = None
    item_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    category: str
    strength: str
    dosage_form: str
    price: int


class NonSurgicalItemUpdate(BaseModel):
    item_code: str
    item_name: str
    item_type: str
    specification: Optional[str] = None
    usage_per_patient: float = 1.0
    unit_of_measure: str


class NonSurgicalBatchUpdate(BaseModel):
    batch_number: Optional[str] = None
    quantity_available: Optional[int] = None
    expiry_date: Optional[date] = None
    cost_price: Optional[float] = None
    non_surgical_item_id: Optional[int] = None
    rack_shelf_number: Optional[str] = None

#
class SurgicalItemUpdate(BaseModel):
    item_code: str
    item_name: str
    item_type: str
    size_specification: Optional[str] = None
    sterility_status: str
    usage_count_per_procedure: int = 1
    unit_of_measure: str


class SurgicalBatchUpdate(BaseModel):
    batch_number: Optional[str] = None
    quantity_available: Optional[int] = None
    expiry_date: Optional[date] = None
    cost_price: Optional[float] = None
    surgical_item_id: Optional[int] = None
    rack_shelf_number: Optional[str] = None

# class PharmacyIssueCreate(BaseModel):
#     item_type: str = Field(..., description="medicine | surgical | non_surgical")
#     reference_id: int = Field(..., gt=0, description="Prescription/Procedure/Patient ID")
#     item_id: int = Field(..., gt=0, description="Item ID")
#     quantity: int = Field(..., gt=0, description="Quantity to issue")
#     patient_type: str = Field(..., description="OPD | IPD | Procedure")



class PharmacyIssueRead(BaseModel):
    id: int
    hospital_id: int
    branch_id: int
    item_type: str
    item_id: int
    batch_type: str
    batch_id: int
    patient_type: str
    reference_id: int
    quantity: int
    rate_per_unit: float
    issue_value: float
    issued_by: str
    issued_at: datetime
    is_cancelled: bool

    model_config = ConfigDict(from_attributes=True)

class IssueItemLine(BaseModel):
    item_type: str = Field(..., description="medicine | surgical | non_surgical")
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class IssueRequest(BaseModel):
    reference_id: int = Field(..., gt=0)
    patient_type: str = Field(..., description="OPD | IPD | Procedure")
    items: List[IssueItemLine]

class IssueSummary(BaseModel):
    period: str
    item_type: Optional[str] = None
    total_issues: int
    total_quantity: int
    total_value: float
    issues: List[IssueItemLine]

class PharmacyIssueResponse(BaseModel):
    transaction_type: str
    balance_qty: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
