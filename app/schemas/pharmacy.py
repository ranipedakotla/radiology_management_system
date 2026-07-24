# from pydantic import BaseModel, Field
# from typing import List, Optional, Dict


# #SALE ITEM (ONE MEDICINE LINE IN A BILL)
# class SaleItemCreate(BaseModel):
#     medicine_id: int = Field(
#         ...,
#         example=456,
#         description="Medicine ID from medicines table"
#     )
#     quantity: int = Field(
#         ...,
#         gt=0,
#         example=2,
#         description="Quantity of medicine to sell"
#     )


# #SALE CREATE (OUTSIDE PHARMACY SALE)
# class SaleCreate(BaseModel):
#     items: List[SaleItemCreate]

#     payment_mode: str = Field(
#         ...,
#         example="cash",
#         description="Payment mode: cash / upi / card"
#     )

#     prescription_id: Optional[int] = Field(
#         None,
#         example=456,
#         description="Prescription ID (required for H / H1 / X medicines)"
#     )

#     denominations: Optional[Dict[int, int]] = Field(
#         default=None,
#         example={
#             2000: 1,
#             500: 1,
#             100: 2
#         },
#         description=(
#             "Cash denominations. "
#             "Key = currency note, Value = count. "
#             "Required only when payment_mode is cash."
#         )
#     )

#     model_config = {
#         "json_schema_extra": {
#             "example": {
#                 "items": [
#                     {
#                         "medicine_id": 456,
#                         "quantity": 2
#                     }
#                 ],
#                 "payment_mode": "cash",
#                 "prescription_id": 456,
#                 "denominations": {
#                     2000: 1,
#                     500: 1,
#                     100: 2
#                 }
#             }
#         }
#     }

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict
from enum import Enum


# ==============================
# PAYMENT MODE ENUM
# ==============================
class PaymentMode(str, Enum):
    CASH = "cash"
    UPI = "upi"
    CARD = "card"


# ==============================
# SALE ITEM (ONE MEDICINE LINE)
# ==============================
class SaleItemCreate(BaseModel):
    medicine_id: int = Field(
        ...,
        gt=0,
        example=456,
        description="Medicine ID from medicines table"
    )

    quantity: int = Field(
        ...,
        gt=0,
        example=2,
        description="Quantity of medicine to sell"
    )


# ==============================
# SALE CREATE (OUTSIDE PHARMACY)
# ==============================
class SaleCreate(BaseModel):

    items: List[SaleItemCreate] = Field(
        ...,
        min_length=1,
        description="List of medicines included in sale"
    )

    payment_mode: PaymentMode = Field(
        ...,
        example="cash",
        description="Payment mode: cash / upi / card"
    )

    prescription_id: Optional[int] = Field(
        None,
        gt=0,
        example=456,
        description="Prescription ID (required for H / H1 / X medicines)"
    )

    # denominations: Optional[Dict[int, int]] = Field(
    #     default=None,
    #     example={
    #         2000: 1,
    #         500: 1,
    #         100: 2
    #     },
    #     description=(
    #         "Cash denominations. "
    #         "Key = currency note, Value = count. "
    #         "Required only when payment_mode is cash."
    #     )
    # )
    #
    # # ==============================
    # # VALIDATIONS
    # # ==============================
    # @model_validator(mode="after")
    # def validate_payment_rules(self):
    #     """
    #     Business Rules:
    #     1. Denominations required only for cash payments
    #     2. Denominations NOT allowed for UPI/Card
    #     3. Notes and counts must be positive
    #     """
    #
    #     # CASH VALIDATION
    #     if self.payment_mode == PaymentMode.CASH:
    #         if not self.denominations:
    #             raise ValueError(
    #                 "Denominations are required for cash payments"
    #             )
    #
    #         for note, count in self.denominations.items():
    #             if note <= 0 or count <= 0:
    #                 raise ValueError(
    #                     "Denomination values must be positive integers"
    #                 )
    #
    #     # NON-CASH VALIDATION
    #     else:
    #         if self.denominations:
    #             raise ValueError(
    #                 "Denominations allowed only for cash payments"
    #             )
    #
    #     return self
    #
    # # ==============================
    # # EXAMPLE FOR SWAGGER
    # # ==============================
    # model_config = {
    #     "json_schema_extra": {
    #         "example": {
    #             "items": [
    #                 {
    #                     "medicine_id": 456,
    #                     "quantity": 2
    #                 }
    #             ],
    #             "payment_mode": "cash",
    #             "prescription_id": 456,
    #             "denominations": {
    #                 2000: 1,
    #                 500: 1,
    #                 100: 2
    #             }
    #         }
    #     }
    # }

    # ✅ UPDATED: optional + supports full denomination set
    denominations: Optional[Dict[int, int]] = Field(
        default=None,
        description="Cash denominations (only for CASH payments)"
    )

    @model_validator(mode="after")
    def validate_payment_rules(self):

        allowed_notes = {2000, 500, 200, 100, 50, 20, 10, 5, 2, 1}

        if self.payment_mode == PaymentMode.CASH:

            if not self.denominations:
                raise ValueError("Denominations required for cash payments")

            for note, count in self.denominations.items():

                # ✅ check valid currency note
                if int(note) not in allowed_notes:
                    raise ValueError(f"Invalid denomination: {note}")

                # ✅ must be positive
                if count <= 0:
                    raise ValueError("Denomination counts must be positive integers")

        else:
            if self.denominations:
                raise ValueError("Denominations allowed only for cash payments")

        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {"medicine_id": 1, "quantity": 2}
                ],
                "payment_mode": "cash",
                "prescription_id": 1,
                "denominations": {
                    "500": 2,
                    "100": 3,
                    "50": 1,
                    "20":1,
                    "10":1,
                    "5":1,
                    "2":1,
                    "1":1
                }
            }
        }
    }