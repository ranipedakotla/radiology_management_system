from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict
from enum import Enum


class ReturnTypeEnum(str, Enum):
    REFUND = "REFUND"
    REPLACEMENT = "REPLACEMENT"


class ReturnItemCreate(BaseModel):
    sale_item_id: int = Field(
        ...,
        example=123,
        description="SaleItem ID from original sale"
    )
    quantity: int = Field(
        ...,
        gt=0,
        example=1,
        description="Quantity to return"                     
    )


class RefundCreate(BaseModel):
    refund_mode: str = Field(
        ...,
        example="cash",
        description="Refund mode: cash / upi / card"
    )

    amount: float = Field(
        ...,
        gt=0,
        example=150.0,
        description="Refund amount"
    )

    denominations: Optional[Dict[int, int]] = Field(
        default=None,
        example={100: 1, 50: 1},
        description="Required only for cash refunds"
    )

    @model_validator(mode="after")
    def validate_cash_refund(self):
        if self.refund_mode == "cash" and not self.denominations:
            raise ValueError("Cash refunds require denominations")
        return self


class ReturnCreate(BaseModel):
    sale_id: int = Field(
        ...,
        example=101,
        description="Original Sale ID"
    )

    return_type: ReturnTypeEnum = Field(
        ...,
        example="REFUND"
    )

    reason: Optional[str] = Field(
        None,
        example="Medicine not required"
    )

    items: List[ReturnItemCreate]

    refund: Optional[RefundCreate] = None

    @model_validator(mode="after")
    def validate_refund_requirement(self):
        if self.return_type == ReturnTypeEnum.REFUND and not self.refund:
            raise ValueError("Refund details are required for REFUND type")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "sale_id": 101,
                "return_type": "REFUND",
                "reason": "Medicine not required",
                "items": [
                    {
                        "sale_item_id": 123,
                        "quantity": 1
                    }
                ],
                "refund": {
                    "refund_mode": "cash",
                    "amount": 150.0,
                    "denominations": {
                        100: 1,
                        50: 1
                    }
                }
            }
        }
    }
