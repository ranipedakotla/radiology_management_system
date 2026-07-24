# from pydantic import BaseModel, ConfigDict
# from datetime import date
# from enum import Enum
# from typing import Optional, List
#
#
# class PharmacyType(str, Enum):
#     OPD = "OPD"
#     IPD = "IPD"
#     OUTSIDE = "OUTSIDE"
#
# class MedicineCategory(str, Enum):
#     NORMAL = "NORMAL"
#     SCHEDULE_H = "SCHEDULE_H"
#     SCHEDULE_H1 = "SCHEDULE_H1"
#     SCHEDULE_X = "SCHEDULE_X"
#
# class PrescriptionCreate(BaseModel):
#     doctor_name: str
#     doctor_reg_no: str
#     prescription_date: date
#     image_url: str
#
# # class PharmacyIssueCreate(BaseModel):
# #     pharmacy_type: PharmacyType
# #     medicine_id: int
# #     prescription_id: int | None
# #     patient_name: str
# #     patient_id_proof: str
# #     quantity: int
# #     pharmacist_sign: str
# class IssueItem(BaseModel):
#     item_type: str  # medicine | surgical | non_surgical
#     item_id: int
#     quantity: int
#
#
# class PharmacyIssueCreate(BaseModel):
#     pharmacy_type: str
#     prescription_id: Optional[int] = None
#     patient_type: str
#     patient_name: str
#     patient_id_proof: str
#     pharmacist_sign: str
#     visit_id: int
#     prescription_id: int
#     item_type: str
#     hospital_id: int
#     branch_id: int
#
#     items: List[IssueItem]
# # class PharmacyIssueResponse(PharmacyIssueCreate):
# #     id: int
# #
# #     model_config = ConfigDict(from_attributes=True)
# class PharmacyIssueResponse(BaseModel):
#     id: int
#     status: str
#     reference_id: int
#     patient_type: str
#     items: list
#
#
#     model_config = ConfigDict(from_attributes=True)
#
# class CashDenominationCreate(BaseModel):
#     note_2000: int = 0
#     note_500: int = 0
#     note_200: int = 0
#     note_100: int = 0
#     note_50: int = 0
#     note_20: int = 0
#     note_10: int = 0
#     coins: float = 0
#
# class CashFlowCreate(BaseModel):
#     reference_type: str
#     reference_id: int
#     payment_mode: str  # CASH / UPI
#     amount: float
#     upi_app: Optional[str] = None
#     denominations: Optional[CashDenominationCreate] = None
#     model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from datetime import date
from enum import Enum
from typing import Optional, List


class PharmacyType(str, Enum):
    OPD = "OPD"
    IPD = "IPD"
    OUTSIDE = "OUTSIDE"

class MedicineCategory(str, Enum):
    NORMAL = "NORMAL"
    SCHEDULE_H = "SCHEDULE_H"
    SCHEDULE_H1 = "SCHEDULE_H1"
    SCHEDULE_X = "SCHEDULE_X"

class PrescriptionCreate(BaseModel):
    doctor_name: str
    doctor_reg_no: str
    prescription_date: date
    image_url: str

# class PharmacyIssueCreate(BaseModel):
#     pharmacy_type: PharmacyType
#     medicine_id: int
#     prescription_id: int | None
#     patient_name: str
#     patient_id_proof: str
#     quantity: int
#     pharmacist_sign: str
class IssueItem(BaseModel):
    item_type: str  # medicine | surgical | non_surgical
    item_id: int
    quantity: int


class PharmacyIssueCreate(BaseModel):
    pharmacy_type: str
    prescription_id: Optional[int] = None
    patient_type: str
    patient_name: str
    patient_id_proof: str
    pharmacist_sign: str
    visit_id: int
    prescription_id: int
    item_type: str
    hospital_id: int
    branch_id: int

    batch_id: Optional[int] = None
    item_id: Optional[int] = None
    batch_type: Optional[str] = None

    items: List[IssueItem]
# class PharmacyIssueResponse(PharmacyIssueCreate):
#     id: int
#
#     model_config = ConfigDict(from_attributes=True)
class PharmacyIssueResponse(BaseModel):
    id: int
    status: str
    reference_id: int
    patient_type: str
    items: list


    model_config = ConfigDict(from_attributes=True)

class CashDenominationCreate(BaseModel):
    note_2000: int = 0
    note_500: int = 0
    note_200: int = 0
    note_100: int = 0
    note_50: int = 0
    note_20: int = 0
    note_10: int = 0
    coins: float = 0

class CashFlowCreate(BaseModel):
    reference_type: str
    reference_id: int
    payment_mode: str  # CASH / UPI
    amount: float
    upi_app: Optional[str] = None
    denominations: Optional[CashDenominationCreate] = None
    model_config = ConfigDict(from_attributes=True)