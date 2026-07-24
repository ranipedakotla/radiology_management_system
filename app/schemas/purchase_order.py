
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional

# class POBase(BaseModel):
#                     vendor_id: int
#                     medicine_id: int
#                     quantity: int
#                     rate: float
#                     discount: float
#                     gst: float
#                     delivery_location: str
#                     delivery_deadline: date
#                     terms: str
#
#
#
# class PurchaseOrderCreate(BaseModel):
#     po_number: str
#
#     vendor_id: int = Field(..., gt=0)
#     medicine_id: int = Field(..., gt=0)
#
#     quantity: int = Field(..., gt=0)
#     rate: float = Field(..., ge=0)
#
#     discount: float = Field(0, ge=0)
#     gst: float = Field(0, ge=0)
#
#     delivery_location: str
#     delivery_deadline: date
#     terms: str
#
#
# class POUpdate(BaseModel):
#     vendor_id: Optional[int] = Field(None, gt=0)
#     medicine_id: Optional[int] = Field(None, gt=0)
#
#     quantity: Optional[int] = None
#     rate: Optional[float] = None
#     discount: Optional[float] = None
#     gst: Optional[float] = None
#
#     delivery_location: Optional[str] = None
#     delivery_deadline: Optional[date] = None
#     terms: Optional[str] = None
#
#
# class POOut(POBase):
#         id: int
#         po_number: str
# model_config = ConfigDict(from_attributes=True)
# app/schemas/purchase_order.py

from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional


class POBase(BaseModel):
    vendor_id: int = Field(..., gt=0)
    medicine_id: int = Field(..., gt=0)

    quantity: int = Field(..., gt=0)
    rate: float = Field(..., ge=0)

    discount: float = Field(0, ge=0)
    gst: float = Field(0, ge=0)

    delivery_location: Optional[str] = None
    delivery_deadline: Optional[date] = None
    terms: Optional[str] = None


class POCreate(POBase):
    pass


class POUpdate(BaseModel):
    vendor_id: Optional[int] = Field(None, gt=0)
    medicine_id: Optional[int] = Field(None, gt=0)

    quantity: Optional[int] = None
    rate: Optional[float] = None
    discount: Optional[float] = None
    gst: Optional[float] = None

    delivery_location: Optional[str] = None
    delivery_deadline: Optional[date] = None
    terms: Optional[str] = None


class POOut(POBase):
    id: int
    po_number: str

    model_config = ConfigDict(from_attributes=True)
