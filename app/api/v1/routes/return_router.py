from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.sql import select

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import async_get_db, require_roles, get_current_user
from app.models.auth import User
from app.models.user_models import Sale, SaleItem
from app.models.entry_models import Medicine, Batch
from app.models.pharmacy import MedicineCategory
from app.models.returns import ReturnType, Refund, ReturnItem, Return
from app.schemas.returns import ReturnCreate, ReturnTypeEnum

router = APIRouter(
    prefix="/returns",
    tags=["Returns & Replacements"],
    dependencies=[Depends(require_roles("superadmin"))]
)

OPD_RETURN_DAYS = 7

#
# @router.post("/")
# async def create_return(
#     data: ReturnCreate,
#     hospital_id: int,
#     branch_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#     # --------------------------------------------------
#     # STEP 1: FETCH & VALIDATE SALE
#     # --------------------------------------------------
#     sale = await db.get(Sale, data.sale_id)
#     if not sale:
#         raise HTTPException(status_code=404, detail="Sale not found")
#
#     # MULTI-TENANT VALIDATION
#     if sale.hospital_id != hospital_id or sale.branch_id != branch_id:
#         raise HTTPException(
#             status_code=403,
#             detail="Sale does not belong to this hospital/branch"
#         )
#
#     # OPD RETURN WINDOW CHECK
#     if sale.created_at < datetime.utcnow() - timedelta(days=OPD_RETURN_DAYS):
#         raise HTTPException(
#             status_code=400,
#             detail="Return window expired (7 days OPD policy)"
#         )
#
#     # --------------------------------------------------
#     # STEP 2: CREATE RETURN HEADER
#     # --------------------------------------------------
#     return_entry = Return(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         sale_id=data.sale_id,
#         return_type=ReturnType[data.return_type],
#         reason=data.reason
#     )
#
#     db.add(return_entry)
#     await db.flush()
#
#     total_refund_amount = 0.0
#
#     # --------------------------------------------------
#     # STEP 3: PROCESS EACH RETURN ITEM
#     # --------------------------------------------------
#     for item in data.items:
#
#         sale_item = await db.get(SaleItem, item.sale_item_id)
#         if not sale_item:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Invalid sale_item_id: {item.sale_item_id}"
#             )
#
#         if sale_item.sale_id != sale.id:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Sale item does not belong to this sale"
#             )
#
#         if item.quantity > sale_item.quantity:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Return quantity exceeds sold quantity"
#             )
#
#         medicine = await db.get(Medicine, sale_item.medicine_id)
#
#         # Schedule X drugs not returnable
#         if medicine.category == MedicineCategory.SCHEDULE_X:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"{medicine.name} is not returnable"
#             )
#
#         # Create return item
#         return_item = ReturnItem(
#             return_id=return_entry.id,
#             sale_item_id=sale_item.id,
#             quantity=item.quantity,
#             batch_id=sale_item.batch_id
#         )
#         db.add(return_item)
#
#         # --------------------------------------------------
#         # RESTORE STOCK (ONLY SAME BRANCH)
#         # --------------------------------------------------
#         batch = await db.get(Batch, sale_item.batch_id)
#
#         if batch.branch_id != branch_id:
#             raise HTTPException(
#                 status_code=403,
#                 detail="Batch belongs to different branch"
#             )
#
#         batch.quantity += item.quantity
#
#         total_refund_amount += sale_item.price * item.quantity
#
#     # --------------------------------------------------
#     # STEP 4: REFUND LOGIC
#     # --------------------------------------------------
#     if data.return_type == "REFUND":
#
#         if not data.refund:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Refund details required for REFUND type"
#             )
#
#         if round(data.refund.amount, 2) != round(total_refund_amount, 2):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Refund amount mismatch"
#             )
#
#         # CASH AUDIT VALIDATION
#         if data.refund.refund_mode.lower() == "cash":
#
#             if not data.refund.denominations:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Cash denominations required"
#                 )
#
#             total_cash = sum(
#                 int(note) * count
#                 for note, count in data.refund.denominations.items()
#             )
#
#             if total_cash != int(total_refund_amount):
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Cash denominations total mismatch"
#                 )
#
#         refund = Refund(
#             return_id=return_entry.id,
#             amount=total_refund_amount,
#             refund_mode=data.refund.refund_mode,
#             denominations=data.refund.denominations
#         )
#
#         db.add(refund)
#
#     # --------------------------------------------------
#     # STEP 5: FINALIZE
#     # --------------------------------------------------
#     await db.commit()
#
#     return {
#         "return_id": return_entry.id,
#         "hospital_id": hospital_id,
#         "branch_id": branch_id,
#         "type": data.return_type,
#         "refund_amount": total_refund_amount
#         if data.return_type == "REFUND" else 0,
#         "message": "Return processed successfully"
#     }

#
# @router.post("/")
# async def create_return(
#     data: ReturnCreate,
#     hospital_id: int,
#     branch_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#
#     # -------------------------------
#     # STEP 1: FETCH SALE
#     # -------------------------------
#     sale = await db.get(Sale, data.sale_id)
#     if not sale:
#         raise HTTPException(status_code=404, detail="Sale not found")
#
#     if sale.hospital_id != hospital_id or sale.branch_id != branch_id:
#         raise HTTPException(status_code=403, detail="Sale does not belong to this hospital/branch")
#
#     if sale.created_at < datetime.utcnow() - timedelta(days=OPD_RETURN_DAYS):
#         raise HTTPException(status_code=400, detail="Return window expired (7 days OPD policy)")
#
#     # -------------------------------
#     # STEP 2: CREATE RETURN HEADER
#     # -------------------------------
#     return_entry = Return(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         sale_id=data.sale_id,
#         return_type=data.return_type,   # FIXED (no Enum indexing)
#         reason=data.reason
#     )
#
#     db.add(return_entry)
#     await db.flush()
#
#     total_refund_amount = Decimal("0.00")
#
#     # -------------------------------
#     # STEP 3: PROCESS ITEMS
#     # -------------------------------
#     for item in data.items:
#
#         sale_item = await db.get(SaleItem, item.sale_item_id)
#         if not sale_item:
#             raise HTTPException(400, f"Invalid sale_item_id: {item.sale_item_id}")
#
#         if sale_item.sale_id != sale.id:
#             raise HTTPException(400, "Sale item does not belong to this sale")
#
#         if item.quantity > sale_item.quantity:
#             raise HTTPException(400, "Return quantity exceeds sold quantity")
#
#         medicine = await db.get(Medicine, sale_item.medicine_id)
#
#         if medicine.category == MedicineCategory.SCHEDULE_X:
#             raise HTTPException(400, f"{medicine.item_name} is not returnable")
#
#         # -------------------------------
#         # RESTORE STOCK
#         # -------------------------------
#         batch = await db.get(Batch, sale_item.batch_id)
#
#         if batch.branch_id != branch_id:
#             raise HTTPException(403, "Batch belongs to different branch")
#
#         batch.quantity_available += item.quantity
#
#         # -------------------------------
#         # FIXED REFUND CALCULATION
#         # -------------------------------
#         # line_refund = (
#         #     Decimal(str(sale_item.price)) *
#         #     Decimal(str(item.quantity))
#         # ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
#         #
#         # total_refund_amount += line_refund
#
#         line_total = Decimal(str(sale_item.price or 0))
#
#         refund_line = line_total * Decimal(str(item.quantity))
#
#         total_refund_amount += refund_line
#
#         print("SALE ITEM:", sale_item.id, sale_item.price, item.quantity)
#
#         # -------------------------------
#         # CREATE RETURN ITEM
#         # -------------------------------
#         db.add(ReturnItem(
#             return_id=return_entry.id,
#             sale_item_id=sale_item.id,
#             quantity=item.quantity,
#             batch_id=sale_item.batch_id
#         ))
#
#     # -------------------------------
#     # STEP 4: VALIDATE REFUND
#     # -------------------------------
#     if data.return_type == ReturnType.REFUND:
#
#         if not data.refund:
#             raise HTTPException(400, "Refund details required")
#
#         refund_amount = Decimal(str(data.refund.amount)).quantize(Decimal("0.01"))
#
#         if refund_amount != total_refund_amount:
#             raise HTTPException(
#                 400,
#                 detail=f"Refund amount mismatch. Expected={total_refund_amount}, Got={refund_amount}"
#             )
#
#         # -------------------------------
#         # CASH VALIDATION (FIXED)
#         # -------------------------------
#         if data.refund.refund_mode.lower() == "cash":
#
#             if not data.refund.denominations:
#                 raise HTTPException(400, "Cash denominations required")
#
#             total_cash = sum(
#                 Decimal(str(note)) * Decimal(str(count))
#                 for note, count in data.refund.denominations.items()
#                 if count > 0
#             ).quantize(Decimal("0.01"))
#
#             if total_cash != total_refund_amount:
#                 raise HTTPException(
#                     400,
#                     detail=f"Cash mismatch. Paid={total_cash}, Expected={total_refund_amount}"
#                 )
#
#         # -------------------------------
#         # SAVE REFUND
#         # -------------------------------
#         db.add(Refund(
#             return_id=return_entry.id,
#             amount=float(total_refund_amount),
#             refund_mode=data.refund.refund_mode,
#             denominations=data.refund.denominations
#         ))
#
#     # -------------------------------
#     # FINAL COMMIT
#     # -------------------------------
#     await db.commit()
#
#     return {
#         "return_id": return_entry.id,
#         "hospital_id": hospital_id,
#         "branch_id": branch_id,
#         "type": data.return_type,
#         "refund_amount": float(total_refund_amount) if data.return_type == ReturnType.REFUND else 0,
#         "message": "Return processed successfully"
#     }



# @router.post("/")
# async def create_return(
#     data: ReturnCreate,
#     hospital_id: int,
#     branch_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#
#     # -------------------------------
#     # STEP 1: SALE VALIDATION
#     # -------------------------------
#     sale = await db.get(Sale, data.sale_id)
#     if not sale:
#         raise HTTPException(404, "Sale not found")
#
#     if sale.hospital_id != hospital_id or sale.branch_id != branch_id:
#         raise HTTPException(403, "Sale does not belong to this branch")
#
#     if sale.created_at < datetime.utcnow() - timedelta(days=OPD_RETURN_DAYS):
#         raise HTTPException(400, "Return window expired")
#
#     # -------------------------------
#     # STEP 2: RETURN HEADER
#     # -------------------------------
#     return_entry = Return(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         sale_id=data.sale_id,
#         return_type=data.return_type,
#         reason=data.reason
#     )
#
#     db.add(return_entry)
#     await db.flush()
#
#     total_refund_amount = Decimal("0.00")
#
#     # -------------------------------
#     # STEP 3: PROCESS ITEMS
#     # -------------------------------
#     for item in data.items:
#
#         result = await db.execute(
#             select(SaleItem).where(
#                 SaleItem.id == item.sale_item_id,
#                 SaleItem.sale_id == sale.id
#             )
#         )
#         sale_item = result.scalars().first()
#
#         if not sale_item:
#             raise HTTPException(400, f"Invalid sale_item_id={item.sale_item_id}")
#
#         if item.quantity > sale_item.quantity:
#             raise HTTPException(400, "Return quantity exceeds sold quantity")
#
#         medicine = await db.get(Medicine, sale_item.medicine_id)
#         if not medicine:
#             raise HTTPException(404, "Medicine not found")
#
#         if medicine.category == MedicineCategory.SCHEDULE_X:
#             raise HTTPException(400, f"{medicine.item_name} not returnable")
#
#         # -------------------------------
#         # STOCK RESTORE
#         # -------------------------------
#         batch = await db.get(Batch, sale_item.batch_id)
#         if not batch:
#             raise HTTPException(404, "Batch not found")
#
#         if batch.branch_id != branch_id:
#             raise HTTPException(403, "Batch belongs to different branch")
#
#         batch.quantity_available += item.quantity
#
#         # -------------------------------
#         # FIXED PRICE LOGIC (IMPORTANT)
#         # -------------------------------
#         price_value = (
#             medicine.unit_price
#             if medicine.unit_price not in (None, 0)
#             else medicine.price
#         )
#
#         if price_value is None or price_value <= 0:
#             raise HTTPException(
#                 400,
#                 detail=f"Invalid price for medicine_id={medicine.id}"
#             )
#
#         price = Decimal(str(price_value))
#         qty = Decimal(str(item.quantity))
#
#         refund_line = (price * qty).quantize(
#             Decimal("0.01"),
#             rounding=ROUND_HALF_UP
#         )
#
#         total_refund_amount += refund_line
#
#         # -------------------------------
#         # RETURN ITEM
#         # -------------------------------
#         db.add(ReturnItem(
#             return_id=return_entry.id,
#             sale_item_id=sale_item.id,
#             quantity=item.quantity,
#             batch_id=sale_item.batch_id
#         ))
#
#     # -------------------------------
#     # STEP 4: REFUND VALIDATION
#     # -------------------------------
#     if data.return_type == ReturnType.REFUND:
#
#         if not data.refund:
#             raise HTTPException(400, "Refund details required")
#
#         refund_amount = Decimal(str(data.refund.amount)).quantize(
#             Decimal("0.01"),
#             rounding=ROUND_HALF_UP
#         )
#
#         expected = total_refund_amount.quantize(Decimal("0.01"))
#
#         if refund_amount != expected:
#             raise HTTPException(
#                 400,
#                 detail=f"Refund mismatch. Expected={expected}, Got={refund_amount}"
#             )
#
#         # -------------------------------
#         # CASH VALIDATION
#         # -------------------------------
#         if data.refund.refund_mode.lower() == "cash":
#
#             if not data.refund.denominations:
#                 raise HTTPException(400, "Cash denominations required")
#
#             total_cash = sum(
#                 Decimal(str(note)) * Decimal(str(count))
#                 for note, count in data.refund.denominations.items()
#                 if count > 0
#             ).quantize(Decimal("0.01"))
#
#             if total_cash != expected:
#                 raise HTTPException(
#                     400,
#                     detail=f"Cash mismatch. Paid={total_cash}, Expected={expected}"
#                 )
#
#         # -------------------------------
#         # SAVE REFUND
#         # -------------------------------
#         db.add(Refund(
#             return_id=return_entry.id,
#             amount=float(expected),
#             refund_mode=data.refund.refund_mode,
#             denominations=data.refund.denominations
#         ))
#
#     # -------------------------------
#     # FINAL COMMIT
#     # -------------------------------
#     await db.commit()
#
#     return {
#         "return_id": return_entry.id,
#         "hospital_id": hospital_id,
#         "branch_id": branch_id,
#         "type": data.return_type,
#         "refund_amount": float(total_refund_amount)
#         if data.return_type == ReturnType.REFUND else 0,
#         "message": "Return processed successfully"
#     }


TWOPLACES = Decimal("0.01")


@router.post("/")
async def create_return(
    data: ReturnCreate,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user :User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    # -----------------------
    # 1. FETCH SALE
    # -----------------------
    sale = await db.get(Sale, data.sale_id)
    if not sale:
        raise HTTPException(404, "Sale not found")

    if sale.hospital_id != hospital_id or sale.branch_id != branch_id:
        raise HTTPException(403, "Sale not in this branch")

    if sale.created_at < datetime.utcnow() - timedelta(days=OPD_RETURN_DAYS):
        raise HTTPException(400, "Return window expired")

    # -----------------------
    # 2. CREATE RETURN
    # -----------------------
    return_entry = Return(
        hospital_id=hospital_id,
        branch_id=branch_id,
        sale_id=data.sale_id,
        return_type=data.return_type,
        reason=data.reason
    )

    db.add(return_entry)
    await db.flush()

    total_refund = Decimal("0.00")

    # -----------------------
    # 3. PROCESS ITEMS
    # -----------------------
    for item in data.items:

        result = await db.execute(
            select(SaleItem).where(
                SaleItem.id == item.sale_item_id,
                SaleItem.sale_id == sale.id
            )
        )
        sale_item = result.scalars().first()

        if not sale_item:
            raise HTTPException(400, f"Invalid sale_item_id {item.sale_item_id}")

        if item.quantity > sale_item.quantity:
            raise HTTPException(400, "Return qty exceeds sold qty")

        medicine = await db.get(Medicine, sale_item.medicine_id)
        if not medicine:
            raise HTTPException(404, "Medicine missing")

        if medicine.category == MedicineCategory.SCHEDULE_X:
            raise HTTPException(400, "Schedule X not returnable")

        # -----------------------
        # STOCK RESTORE (FIXED)
        # -----------------------
        batch = await db.get(Batch, sale_item.batch_id)

        if not batch:
            raise HTTPException(404, "Batch not found")

        if batch.branch_id != branch_id:
            raise HTTPException(403, "Wrong branch batch")

        # IMPORTANT FIX HERE:
        batch.quantity_available += item.quantity

        # -----------------------
        # PRICE FIX (MAIN BUG FIX)
        # -----------------------
        unit_price = Decimal(str(sale_item.price if sale_item.price else 0))
        if unit_price <= 0:
            raise HTTPException(400, f"Invalid price for sale_item {sale_item.id}")

        line_total = (unit_price * Decimal(item.quantity)).quantize(TWOPLACES)
        total_refund += line_total

        db.add(ReturnItem(
            return_id=return_entry.id,
            sale_item_id=sale_item.id,
            quantity=item.quantity,
            batch_id=sale_item.batch_id
        ))

    # -----------------------
    # 4. REFUND VALIDATION
    # -----------------------
    if data.return_type == ReturnType.REFUND:

        if not data.refund:
            raise HTTPException(400, "Refund required")

        expected = total_refund.quantize(TWOPLACES)
        given = Decimal(str(data.refund.amount)).quantize(TWOPLACES)

        if expected != given:
            raise HTTPException(
                400,
                f"Refund mismatch. Expected={expected}, Got={given}"
            )

        # CASH VALIDATION
        if data.refund.refund_mode.lower() == "cash":

            if not data.refund.denominations:
                raise HTTPException(400, "Cash denominations required")

            cash_total = sum(
                Decimal(str(note)) * Decimal(str(count))
                for note, count in data.refund.denominations.items()
                if count > 0
            ).quantize(TWOPLACES)

            if cash_total != expected:
                raise HTTPException(
                    400,
                    f"Cash mismatch. Paid={cash_total}, Expected={expected}"
                )

        db.add(Refund(
            return_id=return_entry.id,
            amount=float(expected),
            refund_mode=data.refund.refund_mode,
            denominations=data.refund.denominations
        ))

    # -----------------------
    # FINAL
    # -----------------------
    await db.commit()

    return {
        "return_id": return_entry.id,
        "hospital_id": hospital_id,
        "branch_id": branch_id,
        "type": data.return_type,
        "refund_amount": float(total_refund),
        "message": "Return processed successfully"
    }