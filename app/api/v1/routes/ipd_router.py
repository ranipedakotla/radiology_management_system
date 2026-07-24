from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import uuid
import re
from app.core.security import async_get_db
from app.models.ipd_models import MedicineReturn, WardMedicineIssue
from app.models.entry_models import PharmacyIssue
from app.schemas.ipd_schemasp import (
    IPDSupplyRequest,
    IPDSupplyResponse,
    IPDReturnRequest,
    IPDReturnResponse,
    WardIssueOut
)
from app.services.ipd_crud import (
    create_ward_issue,
    create_medicine_return,
    get_issue_by_ref,
    get_issues_by_patient_uhid
)
from app.utils.ipd_security import get_current_pharmacist

router = APIRouter()

# def validate_card_number(card_number: str) -> bool:
#     """Basic Luhn algorithm for card number validation"""
#     cleaned = card_number.replace(' ', '').replace('-', '')
#     if not cleaned or not re.match(r'^\d{13,19}$', cleaned):
#         return False

#     def luhn_checksum(digits: str) -> bool:
#         digits_list = [int(d) for d in digits]
#         checksum = 0
#         digits_list.reverse()
#         for i, digit in enumerate(digits_list):
#             if i % 2 == 1:
#                 doubled = digit * 2
#                 checksum += doubled // 10 + doubled % 10
#             else:
#                 checksum += digit
#         return checksum % 10 == 0

#     return luhn_checksum(cleaned)

def validate_card_number(card_number: str) -> bool:
    cleaned = card_number.replace(" ", "").replace("-", "")
    if not re.match(r"^\d{13,19}$", cleaned):
        return False

    digits = list(map(int, cleaned[::-1]))
    checksum = 0

    for i, d in enumerate(digits):
        if i % 2:
            d *= 2
            checksum += d // 10 + d % 10
        else:
            checksum += d

    return checksum % 10 == 0



def validate_expiry_date(expiry: str) -> bool:
    """
    Validates card expiry in MM/YY format.
    Accepts cards valid through the end of expiry month.
    """

    # Format check → MM/YY
    if not expiry or not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", expiry):
        return False

    try:
        month, year = expiry.split("/")
        month = int(month)
        year = int(year)

        # Convert YY → YYYY (assumes 2000–2099 cards)
        year += 2000

        now = datetime.utcnow()
        current_year = now.year
        current_month = now.month

        # Card valid till END of expiry month
        if year < current_year:
            return False

        if year == current_year and month < current_month:
            return False

        return True

    except Exception:
        return False

# @router.post("/ward-supply", response_model=IPDSupplyResponse, status_code=201)
# async def issue_medicines_to_ward(
#         request: IPDSupplyRequest,
#         db: AsyncSession = Depends(get_db),
#         pharmacist=Depends(get_current_pharmacist)
# ):
#     # Verify patient UHID (allow first issue)
#     result = await db.execute(
#         select(PharmacyIssue).where(PharmacyIssue.patient_uhid == request.patient_uhid)
#     )
#     patient_exists = result.scalars().first() is not None

#     # Allow first issue creation
#     if not patient_exists:
#         patient_exists = True

#     if not patient_exists:
#         raise HTTPException(status_code=404, detail="Patient UHID not found")

#     #validate quantities
#     total_quantity = sum(item.quantity for item in request.medicines)
#     if total_quantity <= 0:
#         raise HTTPException(status_code=400, detail="Invalid medicine quantities")

#     #validate payment mode
#     if request.payment_mode == "cash":
#         if not request.cash_denominations or not any(d.count > 0 for d in request.cash_denominations):
#             raise HTTPException(status_code=400, detail="Valid cash denominations required")
#         paid_amount = sum(d.denomination * d.count for d in request.cash_denominations)
#         if paid_amount < request.total_amount:
#             raise HTTPException(status_code=400, detail=f"Paid ₹{paid_amount} < Total ₹{request.total_amount}")

#     elif request.payment_mode == "card":
#         if not all([request.card_number, request.card_expiry, request.card_cvv, request.card_txn_ref]):
#             raise HTTPException(status_code=400, detail="Card number, expiry, CVV, and transaction ref required")

#         #card validations
#         if not validate_card_number(request.card_number):
#             raise HTTPException(status_code=400, detail="Invalid card number")

#         if not validate_expiry_date(request.card_expiry):
#             raise HTTPException(status_code=400, detail="Invalid or expired card expiry date")

#         if not re.match(r'^\d{3,4}$', request.card_cvv):
#             raise HTTPException(status_code=400, detail="Invalid CVV (3-4 digits)")

#     issue_uuid = uuid.uuid4()
#     medicines_json = json.dumps([item.model_dump() for item in request.medicines])
#     cash_denominations_json = json.dumps(
#         [d.model_dump() for d in request.cash_denominations]
#     ) if request.cash_denominations else None

#     ward_issue = PharmacyIssue(
#         issue_ref=issue_uuid.bytes,
#         patient_uhid=request.patient_uhid,
#         ward_id=request.ward_id,
#         pharmacist_id=pharmacist["id"],
#         medicines_json=medicines_json,
#         total_amount=request.total_amount,
#         noc_number=request.noc_number,
#         payment_mode=request.payment_mode,
#         cash_denominations_json=cash_denominations_json,
#         card_txn_ref=request.card_txn_ref
#     )

#     saved_issue = await create_ward_issue(db, ward_issue)

#     return IPDSupplyResponse(
#         success=True,
#         issue_ref=str(issue_uuid),
#         message="Medicines issued to ward. Patient account auto-billed successfully.",
#         ward_supply={
#             "issue_ref": str(issue_uuid),
#             "patient_uhid": saved_issue.patient_uhid,
#             "ward_id": saved_issue.ward_id,
#             "total_amount": saved_issue.total_amount,
#             "payment_mode": request.payment_mode
#         },
#         payment_mode=request.payment_mode,
#         noc_number=request.noc_number
#     )


# @router.post("/medicine-return", response_model=IPDReturnResponse)
# async def process_medicine_return(
#         request: IPDReturnRequest,
#         db: AsyncSession = Depends(get_db),
#         pharmacist=Depends(get_current_pharmacist)
# ):
#     original_issue = await get_issue_by_ref(db, request.issue_ref)
#     if not original_issue:
#         raise HTTPException(status_code=404, detail="Original issue not found")

#     # Validate return quantities
#     original_medicines = json.loads(original_issue.medicines_json)
#     return_items_dict = {item.medicine_id: item for item in request.return_items}

#     for med_id, return_item in return_items_dict.items():
#         original_qty = next((item["quantity"] for item in original_medicines if item["medicine_id"] == med_id), 0)
#         if return_item.quantity > original_qty:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Return qty {return_item.quantity} > original {original_qty} for medicine {med_id}"
#             )

#     # Calculate refund amount
#     refund_amount = 0.0
#     for orig in original_medicines:
#         med_id = orig["medicine_id"]
#         if med_id in return_items_dict:
#             qty = min(return_items_dict[med_id].quantity, orig["quantity"])
#             refund_amount += qty * orig["unit_price"]

#     # Validate cash refund only
#     if request.refund_mode == "cash":
#         if not request.refund_cash_denominations or not any(d.count > 0 for d in request.refund_cash_denominations):
#             raise HTTPException(status_code=400, detail="Valid refund cash denominations required")
#         refund_paid = sum(d.denomination * d.count for d in request.refund_cash_denominations)
#         if refund_paid < refund_amount:
#             raise HTTPException(status_code=400, detail=f"Refund cash ₹{refund_paid} < amount ₹{refund_amount}")

#     return_uuid = uuid.uuid4()
#     return_items_json = json.dumps([item.model_dump() for item in request.return_items])
#     refund_denominations_json = json.dumps(
#         [d.model_dump() for d in request.refund_cash_denominations]
#     ) if request.refund_cash_denominations else None

#     return_record = MedicineReturn(
#         return_ref=return_uuid.bytes,
#         issue_ref=original_issue.issue_ref,
#         patient_uhid=original_issue.patient_uhid,
#         return_items_json=return_items_json,
#         reason=request.reason,
#         pharmacist_id=pharmacist["id"],
#         noc_number=request.noc_number,
#         refund_mode=request.refund_mode,
#         refund_denominations_json=refund_denominations_json,
#         refund_card_txn_ref=request.refund_card_txn_ref
#     )

#     await create_medicine_return(db, return_record)

#     return IPDReturnResponse(
#         success=True,
#         return_ref=str(return_uuid),
#         message=f"Medicine return accepted. Stock replenished & ₹{refund_amount:.2f} refunded.",
#         reduced_wastage=True,
#         billing_adjusted=True,
#         refund_mode=request.refund_mode,
#         refund_amount=refund_amount,
#         noc_number=request.noc_number
#     )

# @router.post("/ward-supply", response_model=IPDSupplyResponse, status_code=201)
# async def issue_medicines_to_ward(
#     request: IPDSupplyRequest,
#     db: AsyncSession = Depends(get_db),
#     pharmacist=Depends(get_current_pharmacist),
# ):
#     hospital_id = pharmacist.hospital_id
#     branch_id = pharmacist.branch_id
#     pharmacist_id = pharmacist.id
#
#
#     # Verify patient UHID
#     result = await db.execute(
#         select(PharmacyIssue).where(
#             PharmacyIssue.patient_uhid == request.patient_uhid
#         )
#     )
#     patient_exists = result.scalars().first() is not None
#
#     if not patient_exists:
#         patient_exists = True  # allow first issue
#
#     # Quantity validation
#     total_quantity = sum(item.quantity for item in request.medicines)
#     if total_quantity <= 0:
#         raise HTTPException(400, "Invalid medicine quantities")
#
#     #PAYMENT VALIDATION
#     if request.payment_mode == "cash":
#         if not request.cash_denominations or not any(
#             d.count > 0 for d in request.cash_denominations
#         ):
#             raise HTTPException(400, "Valid cash denominations required")
#
#         paid_amount = sum(
#             d.denomination * d.count for d in request.cash_denominations
#         )
#
#         if paid_amount < request.total_amount:
#             raise HTTPException(
#                 400,
#                 f"Paid ₹{paid_amount} < Total ₹{request.total_amount}",
#             )
#
#     elif request.payment_mode == "card":
#         if not all(
#             [
#                 request.card_number,
#                 request.card_expiry,
#                 request.card_cvv,
#                 request.card_txn_ref,
#             ]
#         ):
#             raise HTTPException(400, "Card details required")
#
#         if not validate_card_number(request.card_number):
#             raise HTTPException(400, "Invalid card number")
#
#         if not validate_expiry_date(request.card_expiry.strip()):
#             raise HTTPException(400, "Invalid or expired card")
#
#         if not re.match(r"^\d{3,4}$", request.card_cvv):
#             raise HTTPException(400, "Invalid CVV")
#
#     #CREATE ISSUE
#     issue_uuid = uuid.uuid4()
#
#     medicines_json = json.dumps(
#         [item.model_dump() for item in request.medicines]
#     )
#
#     cash_denominations_json = (
#         json.dumps([d.model_dump() for d in request.cash_denominations])
#         if request.cash_denominations
#         else None
#     )
#
#     ward_issue = WardMedicineIssue(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         issue_ref=issue_uuid.bytes,
#         patient_uhid=request.patient_uhid,
#         ward_id=request.ward_id,
#         pharmacist_id=pharmacist["id"],
#         medicines_json=medicines_json,
#         total_amount=request.total_amount,
#         noc_number=request.noc_number,
#         payment_mode=request.payment_mode,
#         cash_denominations_json=cash_denominations_json,
#         card_txn_ref=request.card_txn_ref,
#     )
#
#     saved_issue = await create_ward_issue(db, ward_issue)
#
#     return IPDSupplyResponse(
#         success=True,
#         issue_ref=str(issue_uuid),
#         message="Medicines issued successfully.",
#         ward_supply={
#             "issue_ref": str(issue_uuid),
#             "patient_uhid": saved_issue.patient_uhid,
#             "ward_id": saved_issue.ward_id,
#             "total_amount": saved_issue.total_amount,
#             "payment_mode": request.payment_mode,
#         },
#         payment_mode=request.payment_mode,
#         noc_number=request.noc_number,
#     )


@router.post("/ward-supply", response_model=IPDSupplyResponse, status_code=201)
async def issue_medicines_to_ward(
    request: IPDSupplyRequest,
    db: AsyncSession = Depends(async_get_db),
    pharmacist=Depends(get_current_pharmacist),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.branch_id
    pharmacist_id = pharmacist.id

    # Quantity validation
    total_quantity = sum(item.quantity for item in request.medicines)
    if total_quantity <= 0:
        raise HTTPException(400, "Invalid medicine quantities")

    # PAYMENT VALIDATION
    if request.payment_mode == "cash":
        if not request.cash_denominations or not any(
            d.count > 0 for d in request.cash_denominations
        ):
            raise HTTPException(400, "Valid cash denominations required")

        paid_amount = sum(
            d.denomination * d.count for d in request.cash_denominations
        )

        if paid_amount < request.total_amount:
            raise HTTPException(
                400,
                f"Paid ₹{paid_amount} < Total ₹{request.total_amount}",
            )

    elif request.payment_mode == "card":
        if not all(
            [
                request.card_number,
                request.card_expiry,
                request.card_cvv,
                request.card_txn_ref,
            ]
        ):
            raise HTTPException(400, "Card details required")

        if not validate_card_number(request.card_number):
            raise HTTPException(400, "Invalid card number")

        if not validate_expiry_date(request.card_expiry.strip()):
            raise HTTPException(400, "Invalid or expired card")

        if not re.match(r"^\d{3,4}$", request.card_cvv):
            raise HTTPException(400, "Invalid CVV")

    # CREATE ISSUE
    issue_uuid = uuid.uuid4()

    # FIX: datetime-safe JSON encoding
    medicines_json = json.dumps(
        jsonable_encoder([item.model_dump() for item in request.medicines])
    )

    cash_denominations_json = (
        json.dumps(
            jsonable_encoder([d.model_dump() for d in request.cash_denominations])
        )
        if request.cash_denominations
        else None
    )

    ward_issue = WardMedicineIssue(
        hospital_id=hospital_id,
        branch_id=branch_id,
        issue_ref=issue_uuid.bytes,
        patient_uhid=request.patient_uhid,
        ward_id=request.ward_id,
        pharmacist_id=pharmacist_id,  # FIXED
        medicines_json=medicines_json,
        total_amount=request.total_amount,
        noc_number=request.noc_number,
        payment_mode=request.payment_mode,
        cash_denominations_json=cash_denominations_json,
        card_txn_ref=request.card_txn_ref,
    )

    saved_issue = await create_ward_issue(db, ward_issue)

    return IPDSupplyResponse(
        success=True,
        issue_ref=str(issue_uuid),
        message="Medicines issued successfully.",
        ward_supply={
            "issue_ref": str(issue_uuid),
            "patient_uhid": saved_issue.patient_uhid,
            "ward_id": saved_issue.ward_id,
            "total_amount": saved_issue.total_amount,
            "payment_mode": request.payment_mode,
        },
        payment_mode=request.payment_mode,
        noc_number=request.noc_number,
    )


@router.post("/medicine-return", response_model=IPDReturnResponse)
async def process_medicine_return(
    request: IPDReturnRequest,
    db: AsyncSession = Depends(async_get_db),
    pharmacist=Depends(get_current_pharmacist),
):
    hospital_id = pharmacist.hospital_id
    branch_id = pharmacist.branch_id


    original_issue = await get_issue_by_ref(
        db,
        request.issue_ref,
        hospital_id,
        branch_id,
    )

    if not original_issue:
        raise HTTPException(404, "Original issue not found")

    original_medicines = json.loads(original_issue.medicines_json)
    return_items_dict = {
        item.medicine_id: item for item in request.return_items
    }

    # Validate quantities
    for med_id, return_item in return_items_dict.items():
        original_qty = next(
            (
                item["quantity"]
                for item in original_medicines
                if item["medicine_id"] == med_id
            ),
            0,
        )

        if return_item.quantity > original_qty:
            raise HTTPException(
                400,
                f"Return qty {return_item.quantity} > original {original_qty}",
            )

    # Refund calculation
    refund_amount = 0.0
    for orig in original_medicines:
        med_id = orig["medicine_id"]

        if med_id in return_items_dict:
            qty = min(
                return_items_dict[med_id].quantity,
                orig["quantity"],
            )
            refund_amount += qty * orig["unit_price"]

    # Cash validation
    if request.refund_mode == "cash":
        if not request.refund_cash_denominations:
            raise HTTPException(400, "Cash refund required")

        refund_paid = sum(
            d.denomination * d.count
            for d in request.refund_cash_denominations
        )

        if refund_paid < refund_amount:
            raise HTTPException(
                400,
                f"Refund cash ₹{refund_paid} < ₹{refund_amount}",
            )

    return_uuid = uuid.uuid4()

    return_record = MedicineReturn(
        hospital_id=hospital_id,
        branch_id=branch_id,
        return_ref=return_uuid.bytes,
        issue_ref=original_issue.issue_ref,
        patient_uhid=original_issue.patient_uhid,
        return_items_json=json.dumps(
            jsonable_encoder([item.model_dump() for item in request.return_items])
        ),
        reason=request.reason,
        pharmacist_id = pharmacist.id,
        noc_number=request.noc_number,
        refund_mode=request.refund_mode,
        refund_denominations_json=json.dumps(
            jsonable_encoder([d.model_dump() for d in request.refund_cash_denominations])
        )
        if request.refund_cash_denominations
        else None,
        refund_card_txn_ref=request.refund_card_txn_ref,
    )

    await create_medicine_return(db, return_record)

    return IPDReturnResponse(
        success=True,
        return_ref=str(return_uuid),
        message=f"Return processed. ₹{refund_amount:.2f} refunded.",
        reduced_wastage=True,
        billing_adjusted=True,
        refund_mode=request.refund_mode,
        refund_amount=refund_amount,
        noc_number=request.noc_number,
    )


@router.get("/supply-history/{patient_uhid}",response_model=List[WardIssueOut])
async def get_patient_supply_history(
    patient_uhid: str,
    db: AsyncSession = Depends(async_get_db),
    pharmacist=Depends(get_current_pharmacist)
):
    return await get_issues_by_patient_uhid(
        db,
        patient_uhid,
        pharmacist.hospital_id,
        pharmacist.branch_id,
    )
