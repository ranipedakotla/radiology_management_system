from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date

from app.core.security import async_get_db
from app.schemas.pharmacy import SaleCreate
from app.models.pharmacy import MedicineCategory
from app.models.user_models import (
    Sale,
    SaleItem
)
from app.models.opd import Prescription
from app.models.auth import User
from app.models.entry_models import Medicine, Batch
from app.core.security import require_roles


router = APIRouter(
    prefix="/pharmacy",
    tags=["Outside Pharmacy"]
)

# =========================================================
# POST: SELL MEDICINES
# =========================================================

# @router.post("/sell")
# async def sell_medicine(
#     data: SaleCreate,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(role_required(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
# ):
#
#     # -----------------------------------------------------
#     # STEP 0: VALIDATE PRESCRIPTION
#     # -----------------------------------------------------
#     prescription = None
#
#     if data.prescription_id:
#         prescription = await db.get(Prescription, data.prescription_id)
#         if not prescription:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid prescription_id"
#             )
#
#     # -----------------------------------------------------
#     # CREATE SALE HEADER
#     # -----------------------------------------------------
#     sale = Sale(
#         payment_mode=data.payment_mode.lower(),
#         prescription_id=data.prescription_id,
#         total_amount=0,
#         hospital_id=user.hospital_id,
#         branch_id=user.branch_id
#
#     )
#
#     db.add(sale)
#     await db.flush()
#
#     sub_total = 0
#
#     # -----------------------------------------------------
#     # PROCESS EACH MEDICINE
#     # -----------------------------------------------------
#     for item in data.items:
#
#         # STEP 1: MEDICINE FETCH
#         med = await db.get(Medicine, item.medicine_id)
#         if not med:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Medicine {item.medicine_id} not found"
#             )
#
#         # STEP 2: PRESCRIPTION REQUIRED CHECK
#         if med.category in [
#             MedicineCategory.SCHEDULE_H,
#             MedicineCategory.SCHEDULE_H1,
#             MedicineCategory.SCHEDULE_X
#         ] and not prescription:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Prescription required for {med.name}"
#             )
#
#         # STEP 3: PRESCRIPTION VALIDITY
#         if prescription:
#             days_old = (date.today() - prescription.prescription_date).days
#
#             if med.category == MedicineCategory.SCHEDULE_H and days_old > 30:
#                 raise HTTPException(400, "Prescription expired (Schedule H)")
#
#             if med.category in [
#                 MedicineCategory.SCHEDULE_H1,
#                 MedicineCategory.SCHEDULE_X
#             ] and days_old > 7:
#                 raise HTTPException(400, "Prescription expired (H1 / X)")
#
#         # -----------------------------------------------------
#         # STEP 4: FEFO BATCH (BRANCH SAFE)
#         # -----------------------------------------------------
#         result = await db.execute(
#             select(Batch)
#             .where(
#                 Batch.medicine_id == med.id,
#                 Batch.quantity > 0,
#                 Batch.hospital_id == user.hospital_id,
#                 Batch.branch_id == user.branch_id
#             )
#             .order_by(Batch.expiry_date.asc())
#         )
#
#         batch = result.scalars().first()
#
#         if not batch or batch.quantity < item.quantity:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Insufficient stock for {med.name}"
#             )
#
#         # Reduce stock
#         batch.quantity -= item.quantity
#
#         # -----------------------------------------------------
#         # STEP 5: BILLING
#         # -----------------------------------------------------
#         unit_price = 100
#         base_price = unit_price * item.quantity
#
#         discount = 10 if med.is_discount_allowed else 0
#         final_price = base_price - discount
#
#         sub_total += final_price
#
#         sale_item = SaleItem(
#             sale_id=sale.id,
#             medicine_id=med.id,
#             batch_id=batch.id,
#             quantity=item.quantity,
#             price=final_price,
#             hospital_id=user.hospital_id,
#             branch_id=user.branch_id
#         )
#
#         db.add(sale_item)
#
#     # -----------------------------------------------------
#     # GST CALCULATION
#     # -----------------------------------------------------
#     GST_RATE = 0.12
#     gst_amount = sub_total * GST_RATE
#     grand_total = sub_total + gst_amount
#
#     # -----------------------------------------------------
#     # PAYMENT VALIDATION
#     # -----------------------------------------------------
#     if sale.payment_mode == "cash":
#
#         if not data.denominations:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Cash denominations required"
#             )
#
#         paid_amount = sum(
#             int(denom) * qty
#             for denom, qty in data.denominations.items()
#         )
#
#         if paid_amount != grand_total:
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Denomination total ({paid_amount}) "
#                        f"does not match bill ({grand_total})"
#             )
#
#         sale.denominations = data.denominations
#     else:
#         sale.denominations = None
#
#     sale.total_amount = grand_total
#
#     await db.commit()
#
#     return {
#         "sale_id": sale.id,
#         "sub_total": sub_total,
#         "gst": gst_amount,
#         "grand_total": grand_total,
#         "payment_mode": sale.payment_mode,
#         "denominations": sale.denominations,
#         "message": "Medicines dispensed successfully"
#     }




TWOPLACES = Decimal("0.01")
RUPEE = Decimal("1.00")


@router.post("/sell")
async def sell_medicine(
    data: SaleCreate,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):

    # 1. Prescription validation
    prescription = None
    if data.prescription_id:
        prescription = await db.get(Prescription, data.prescription_id)
        if not prescription:
            raise HTTPException(400, "Invalid prescription_id")

    # 2. Create Sale HEADER
    sale = Sale(
        payment_mode=data.payment_mode.value,
        prescription_id=data.prescription_id,
        total_amount=Decimal("0.0"),
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        pharmacist_id=user.id,
        shift_log_id=getattr(user, "shift_log_id", None),
        patient_type=getattr(data, "patient_type", None),
    )

    db.add(sale)
    await db.flush()

    subtotal = Decimal("0.0")

    # 3. PROCESS ITEMS
    for item in data.items:

        med = await db.get(Medicine, item.medicine_id)
        if not med:
            raise HTTPException(404, f"Medicine {item.medicine_id} not found")

        price_value = med.unit_price if med.unit_price is not None else med.price

        if price_value is None or price_value <= 0:
            raise HTTPException(400, f"Invalid price for medicine {med.id}")

        unit_price = Decimal(str(price_value))

        # Batch selection
        result = await db.execute(
            select(Batch)
            .where(
                Batch.medicine_id == med.id,
                Batch.hospital_id == user.hospital_id,
                Batch.branch_id == user.current_branch_id,
                Batch.quantity_available > 0
            )
            .order_by(Batch.expiry_date.asc())
        )

        batch = result.scalars().first()

        if not batch or batch.quantity_available < item.quantity:
            raise HTTPException(400, f"Insufficient stock for {med.item_name}")

        batch.quantity_available -= item.quantity


        # PRICING
        base = unit_price * Decimal(item.quantity)

        discount = Decimal("0")
        if med.is_discount_allowed:
            discount = (base * Decimal("0.10")).quantize(TWOPLACES)

        line_total = (base - discount).quantize(TWOPLACES)

        subtotal += line_total

        # line_total ADDED
        db.add(SaleItem(
            sale_id=sale.id,
            medicine_id=med.id,
            batch_id=batch.id,
            quantity=item.quantity,
            price=line_total,
            line_total=line_total
        ))

    # 4. SUBTOTAL CHECK
    if subtotal <= 0:
        raise HTTPException(400, "Subtotal is 0. Check medicine pricing.")

    # 5. GST
    gst = (subtotal * Decimal("0.12")).quantize(TWOPLACES)
    grand_total = (subtotal + gst).quantize(TWOPLACES)

    # 6. CASH FIX
    if sale.payment_mode == "cash":

        if not data.denominations:
            raise HTTPException(400, "Cash denominations required")

        paid = sum(
            int(k) * int(v)
            for k, v in data.denominations.items()
            if v and int(v) > 0
        )

        # CASH ALWAYS INTEGER RUPEES
        bill_rounded = int(round(grand_total))

        if paid != bill_rounded:
            raise HTTPException(
                400,
                detail=f"Denomination mismatch. Paid={paid}, Bill={bill_rounded}"
            )

        sale.denominations = data.denominations

    # -------------------------------
    # 7. FINAL SAVE
    # -------------------------------
    sale.total_amount = grand_total

    await db.commit()
    await db.refresh(sale)

    return {
        "sale_id": sale.id,
        "sub_total": subtotal,
        "gst": gst,
        "grand_total": grand_total,
        "payment_mode": sale.payment_mode,
        "message": "Sale completed successfully"
    }
# =========================================================
# GET SALE BY ID
# =========================================================

# @router.get("/sale/{sale_id}")
# async def get_sale(
#     sale_id: int,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(role_required(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
# ):
#
#     result = await db.execute(
#         select(Sale).where(
#             Sale.id == sale_id,
#             Sale.hospital_id == user.hospital_id,
#             Sale.branch_id == user.branch_id
#         )
#     )
#     sale = result.scalar_one_or_none()
#
#     if not sale:
#         raise HTTPException(404, "Sale not found")
#
#     result = await db.execute(
#         select(SaleItem).where(
#             SaleItem.sale_id == sale.id,
#             SaleItem.hospital_id == user.hospital_id,
#             SaleItem.branch_id == user.branch_id
#         )
#     )
#
#     items = result.scalars().all()
#
#     return {
#         "sale_id": sale.id,
#         "total_amount": sale.total_amount,
#         "payment_mode": sale.payment_mode,
#         "denominations": sale.denominations,
#         "items": [
#             {
#                 "medicine_id": i.medicine_id,
#                 "batch_id": i.batch_id,
#                 "quantity": i.quantity,
#                 "price": i.price
#             }
#             for i in items
#         ]
#     }

@router.get("/sale/{sale_id}")
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):

    # -------------------------
    # GET SALE (WITH SECURITY)
    # -------------------------
    result = await db.execute(
        select(Sale).where(
            Sale.id == sale_id,
            Sale.hospital_id == user.hospital_id,
            Sale.branch_id == user.current_branch_id
        )
    )
    sale = result.scalar_one_or_none()

    if not sale:
        raise HTTPException(404, "Sale not found")

    # -------------------------
    # GET ITEMS (FIXED)
    # -------------------------
    result = await db.execute(
        select(SaleItem).where(
            SaleItem.sale_id == sale.id
        )
    )

    items = result.scalars().all()

    return {
        "sale_id": sale.id,
        "total_amount": sale.total_amount,
        "payment_mode": sale.payment_mode,
        "denominations": sale.denominations,
        "items": [
            {
                "medicine_id": i.medicine_id,
                "batch_id": i.batch_id,
                "quantity": i.quantity,
                "price": i.price,
                # optional if exists:
                "line_total": getattr(i, "line_total", i.price)
            }
            for i in items
        ]
    }

# =========================================================
# LIST SALES (BRANCH SAFE)
# =========================================================

@router.get("/sales")
async def list_sales(
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):

    result = await db.execute(
        select(Sale).where(
            Sale.hospital_id == user.hospital_id,
            Sale.branch_id == user.current_branch_id
        )
    )

    sales = result.scalars().all()

    return [
        {
            "sale_id": s.id,
            "total_amount": s.total_amount,
            "payment_mode": s.payment_mode,
            "created_at": s.created_at
        }
        for s in sales
    ]