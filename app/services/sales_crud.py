from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, UploadFile
from datetime import datetime
from app.models.user_models import ShiftLog, Sale, SaleItem, UserShift
from app.models.auth import User
from app.models.opd import Prescription
from app.models.entry_models import Medicine
from app.models.entry_models import Batch
from app.schemas.rolebased_schemas import SaleCreate
from app.core.security import UPLOAD_DIR

async def start_pharmacist_shift(
    db: AsyncSession,
    user: User,
    shift_name: str
):
    result = await db.execute(
        select(ShiftLog).where(
            ShiftLog.pharmacist_id == user.id,
            ShiftLog.end_time.is_(None)
        )
    )

    if result.scalar_one_or_none():
        raise HTTPException(400, "Open shift already exists")

    today = datetime.utcnow().date()

    result = await db.execute(
        select(UserShift).where(
            UserShift.user_id == user.id,
            UserShift.assigned_date == today
        )
    )

    assigned = result.scalar_one_or_none()

    if not assigned:
        raise HTTPException(403, "No shift assigned")

    shift_log = ShiftLog(
        pharmacist_id=user.id,
        shift_id=assigned.shift_id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        start_time=datetime.utcnow(),
    )

    db.add(shift_log)
    await db.commit()
    await db.refresh(shift_log)

    return shift_log

async def end_pharmacist_shift(
    db: AsyncSession,
    user: User,
    shift_id: int
):
    result = await db.execute(
        select(ShiftLog).where(
            ShiftLog.id == shift_id,
            ShiftLog.pharmacist_id == user.id,
            ShiftLog.hospital_id == user.hospital_id,
            ShiftLog.branch_id == user.current_branch_id,
        )
    )

    shift = result.scalar_one_or_none()

    if not shift:
        raise HTTPException(404, "Shift not found")

    shift.end_time = datetime.utcnow()

    await db.commit()
    await db.refresh(shift)

    return shift
#
# async def create_pharmacy_sale(db: AsyncSession,user: User,payload: SaleCreate):
#     result = await db.execute(
#         select(ShiftLog).where(
#             ShiftLog.pharmacist_id == user.id,
#             ShiftLog.end_time.is_(None),
#             ShiftLog.hospital_id == user.hospital_id,
#             ShiftLog.branch_id == user.branch_id
#         )
#     )
#
#     shift = result.scalar_one_or_none()
#
#     total = sum(i.unit_price * i.quantity for i in payload.items)
#
#     discount_amount = 0.0
#     if payload.discount:
#         if payload.discount.mode == "CASH":
#             discount_amount = min(payload.discount.value, total)
#         else:
#             discount_amount = total * payload.discount.value / 100
#
#     net = total - discount_amount
#
#     sale = Sale(
#         pharmacist_id=user.id,
#         hospital_id=user.hospital_id,
#         branch_id=user.branch_id,
#         shift_log_id=shift.id if shift else None,
#         patient_type=payload.patient_type,
#         patient_id=payload.patient_id,
#         total_amount=total,
#         discount_amount=discount_amount,
#         net_amount=net,
#         payment_mode=payload.payment_mode,
#     )
#
#     db.add(sale)
#     await db.flush()
#
#     for item in payload.items:
#         result = await db.execute(
#             select(Medicine).where(
#                 Medicine.id == item.medicine_id,
#                 Medicine.hospital_id == user.hospital_id,
#                 Medicine.branch_id == user.branch_id,
#             )
#         )
#
#         med = result.scalar_one_or_none()
#
#         if not med or med.stock < item.quantity:
#             raise HTTPException(400, "Insufficient stock")
#
#         med.stock -= item.quantity
#
#         db.add(SaleItem(
#             sale_id=sale.id,
#             medicine_id=item.medicine_id,
#             quantity=item.quantity,
#             unit_price=item.unit_price,
#             line_total=item.quantity * item.unit_price
#         ))
#
#     await db.commit()
#     await db.refresh(sale)
#
#     return sale




async def create_pharmacy_sale(
    db: AsyncSession,
    user: User,
    payload: SaleCreate
):
    result = await db.execute(
        select(ShiftLog).where(
            ShiftLog.pharmacist_id == user.id,
            ShiftLog.end_time.is_(None),
            ShiftLog.hospital_id == user.hospital_id,
            ShiftLog.branch_id == user.current_branch_id
        )
    )

    shift = result.scalar_one_or_none()

    total = sum(i.unit_price * i.quantity for i in payload.items)

    discount_amount = 0.0

    if payload.discount:
        if payload.discount.mode.upper() == "CASH":
            discount_amount = min(payload.discount.value, total)
        else:
            discount_amount = total * payload.discount.value / 100

    net = total - discount_amount

    sale = Sale(
        pharmacist_id=user.id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        shift_log_id=shift.id if shift else None,
        patient_type=payload.patient_type,
        patient_id=payload.patient_id,
        total_amount=total,
        discount_amount=discount_amount,
        net_amount=net,
        payment_mode=payload.payment_mode,
    )

    db.add(sale)
    await db.flush()

    # STOCK DEDUCTION USING BATCH TABLE

    for item in payload.items:

        result = await db.execute(
            select(Batch)
            .where(
                Batch.medicine_id == item.medicine_id,
                Batch.hospital_id == user.hospital_id,
                Batch.branch_id == user.current_branch_id,
                Batch.quantity_available > 0
            )
            .order_by(Batch.expiry_date.asc())  # FIFO
        )

        batches = result.scalars().all()

        if not batches:
            raise HTTPException(
                status_code=400,
                detail=f"Medicine {item.medicine_id} out of stock"
            )

        remaining_qty = item.quantity

        for batch in batches:

            if remaining_qty <= 0:
                break

            available = batch.quantity_available

            if available >= remaining_qty:
                batch.quantity_available -= remaining_qty
                deducted_qty = remaining_qty
                remaining_qty = 0

            else:
                batch.quantity_available = 0
                deducted_qty = available
                remaining_qty -= available

            db.add(SaleItem(
                sale_id=sale.id,
                medicine_id=item.medicine_id,
                quantity=item.quantity,
                price=item.unit_price,
                line_total=item.quantity * item.unit_price
            ))

        if remaining_qty > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for medicine {item.medicine_id}"
            )

    await db.commit()
    await db.refresh(sale)

    return sale

async def upload_prescription(db: AsyncSession,user: User,patient_id: int | None,file: UploadFile):
    UPLOAD_DIR.mkdir(exist_ok=True)

    filename = f"{user.id}_{datetime.utcnow().timestamp()}_{file.filename}"
    path = UPLOAD_DIR / filename

    with open(path, "wb") as f:
        f.write(await file.read())

    pres = Prescription(
        pharmacist_id=user.id,
        hospital_id=user.hospital_id,
        branch_id=user.current_branch_id,
        patient_id=patient_id,
        filename=file.filename,
        file_path=str(path),
        content_type=file.content_type,
    )

    db.add(pres)
    await db.commit()
    await db.refresh(pres)

    return pres