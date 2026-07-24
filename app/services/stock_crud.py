from sqlalchemy import select,func
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.user_models import ApprovalRequest, PurchaseRequest
from app.models.auth import User
from app.models.entry_models import Medicine,Batch
from app.schemas.rolebased_schemas import DispenseRequest, PurchaseRequestCreate


# async def dispense_medicine(
#     db: AsyncSession,
#     user: User,
#     payload: DispenseRequest
# ):
#     result = await db.execute(
#         select(Medicine).where(
#             Medicine.id == payload.medicine_id,
#             Medicine.hospital_id == user.hospital_id,
#             Medicine.branch_id == user.branch_id,
#         )
#     )
#
#     med = result.scalar_one_or_none()
#
#     if not med:
#         raise HTTPException(status_code=404, detail="Medicine not found")
#
#     if med.stock < payload.quantity:
#         raise HTTPException(status_code=400, detail="Insufficient stock")
#
#     # Restricted medicine → approval flow
#     if med.is_restricted:
#         req = ApprovalRequest(
#             pharmacist_id=user.id,
#             medicine_id=med.id,
#             patient_id=payload.patient_id,
#             quantity=payload.quantity,
#             hospital_id=user.hospital_id,
#             branch_id=user.branch_id,
#         )
#
#         db.add(req)
#         await db.commit()
#         await db.refresh(req)
#
#         return {
#             "status": "PENDING_ADMIN_APPROVAL",
#             "request_id": req.id,
#         }
#
#     # Direct dispense
#     med.stock -= payload.quantity
#
#     await db.commit()
#
#     return {
#         "status": "DISPENSED",
#         "new_stock": med.stock,
#     }
#     med.stock -= payload.quantity
#     await db.commit()
#     return {"status": "DISPENSED", "new_stock": med.stock}

async def dispense_medicine(
    db: AsyncSession,
    user,
    payload
):

    # Check medicine exists
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == payload.medicine_id,
            Medicine.hospital_id == user.hospital_id,
            Medicine.branch_id == user.current_branch_id,
        )
    )

    med = result.scalar_one_or_none()

    if not med:
        raise HTTPException(
            status_code=404,
            detail="Medicine not found"
        )

    # Get batches with available stock
    result = await db.execute(
        select(Batch).where(
            Batch.medicine_id == payload.medicine_id,
            Batch.hospital_id == user.hospital_id,
            Batch.branch_id == user.current_branch_id,
            Batch.quantity_available > 0
        ).order_by(Batch.expiry_date.asc())
    )

    batches = result.scalars().all()

    if not batches:
        raise HTTPException(
            status_code=400,
            detail="No stock available"
        )

    total_stock = sum(batch.quantity_available for batch in batches)

    if total_stock < payload.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # Restricted medicine approval
    if med.is_restricted:

        req = ApprovalRequest(
            pharmacist_id=user.id,
            medicine_id=med.id,
            patient_id=payload.patient_id,
            quantity=payload.quantity,
            status="PENDING"
        )

        db.add(req)

        await db.commit()
        await db.refresh(req)

        return {
            "status": "PENDING_ADMIN_APPROVAL",
            "request_id": req.id
        }

    # Dispense using FIFO batch deduction
    remaining_qty = payload.quantity

    for batch in batches:

        if remaining_qty <= 0:
            break

        deduct_qty = min(batch.quantity_available, remaining_qty)

        batch.quantity_available -= deduct_qty

        remaining_qty -= deduct_qty

    await db.commit()

    return {
        "status": "DISPENSED",
        "dispensed_quantity": payload.quantity,
        "remaining_stock": total_stock - payload.quantity
    }



# async def get_low_stock_medicines(
#     db: AsyncSession,
#     user: User
# ):
#     result = await db.execute(
#         select(Medicine).where(
#             Medicine.stock <= Medicine.min_stock,
#             Medicine.hospital_id == user.hospital_id,
#             Medicine.branch_id == user.branch_id,
#         )
#     )
#
#     meds = result.scalars().all()
#
#     low_stock_list = []
#
#     for m in meds:
#
#         if m.stock <= 1:
#             status = "CRITICAL"
#             color = "red"
#             threshold = "1-sheet"
#
#         elif m.stock <= m.min_stock:
#             status = "LOW"
#             color = "orange"
#             threshold = "medium"
#
#         else:
#             status = "FULL"
#             color = "green"
#             threshold = "full"
#
#         low_stock_list.append(
#             {
#                 "id": m.id,
#                 "item_name": m.item_name,
#                 "stock": m.stock,
#                 "min_stock": m.min_stock,
#                 "status": status,
#                 "color": color,
#                 "threshold": threshold,
#             }
#         )
#
#     return low_stock_list

#
# async def get_low_stock_medicines(
#     db: AsyncSession,
#     user: User
# ):
#
#     result = await db.execute(
#         select(Medicine).where(
#             Medicine.hospital_id == user.hospital_id,
#             Medicine.branch_id == user.branch_id,
#         )
#     )
#
#     medicines = result.scalars().all()
#
#     low_stock_list = []
#
#     for m in medicines:
#
#         # Calculate live stock from batches
#         batch_result = await db.execute(
#             select(func.sum(Batch.quantity_available)).where(
#                 Batch.medicine_id == m.id
#             )
#         )
#
#         current_stock = batch_result.scalar() or 0
#
#         # Update master stock automatically
#         m.stock = current_stock
#
#         # Check low stock
#         if current_stock <= m.min_stock:
#
#             if current_stock <= 1:
#                 status = "CRITICAL"
#                 color = "red"
#                 threshold = "1-sheet"
#
#             else:
#                 status = "LOW"
#                 color = "orange"
#                 threshold = "medium"
#
#             low_stock_list.append(
#                 {
#                     "id": m.id,
#                     "item_name": m.item_name,
#                     "stock": current_stock,
#                     "min_stock": m.min_stock,
#                     "status": status,
#                     "color": color,
#                     "threshold": threshold,
#                 }
#             )
#
#     await db.commit()
#
#     return low_stock_list

async def get_low_stock_medicines(
    db: AsyncSession,
    user
):

    # ✅ Single query: get stock per medicine
    stmt = (
        select(
            Medicine.id,
            Medicine.item_name,
            Medicine.min_stock,
            func.coalesce(func.sum(Batch.quantity_available), 0).label("current_stock")
        )
        .outerjoin(Batch, Batch.medicine_id == Medicine.id)
        .where(
            Medicine.hospital_id == user.hospital_id,
            Medicine.branch_id == user.current_branch_id,
        )
        .group_by(Medicine.id, Medicine.item_name, Medicine.min_stock)
    )

    result = await db.execute(stmt)
    rows = result.all()

    low_stock_list = []

    for r in rows:

        current_stock = r.current_stock or 0
        min_stock = r.min_stock or 0

        # low stock check
        if current_stock <= min_stock:

            if current_stock <= 1:
                status = "CRITICAL"
                color = "red"
                threshold = "1-sheet"
            else:
                status = "LOW"
                color = "orange"
                threshold = "medium"

            low_stock_list.append({
                "id": r.id,
                "item_name": r.item_name or "Unknown Medicine",
                "stock": current_stock,
                "min_stock": min_stock,
                "status": status,
                "color": color,
                "threshold": threshold,
            })

    return low_stock_list
#
# async def create_purchase_request(
#     db: AsyncSession,
#     user: User,
#     payload: PurchaseRequestCreate,
# ):
#     pr = PurchaseRequest(
#         pharmacist_id=user.id,
#         medicine_id=payload.medicine_id,
#         quantity=payload.quantity,
#         hospital_id=user.hospital_id,
#         branch_id=user.branch_id,
#     )
#
#     db.add(pr)
#     await db.commit()
#     await db.refresh(pr)
#
#     return pr

async def create_purchase_request(
    db: AsyncSession,
    user: User,
    payload: PurchaseRequestCreate,
):

    pr = PurchaseRequest(
        pharmacist_id=user.id,
        medicine_id=payload.medicine_id,
        quantity=payload.quantity,
        status="PENDING"
    )

    db.add(pr)
    await db.commit()
    await db.refresh(pr)

    return pr
#
# async def get_stock_status(
#     db: AsyncSession,
#     user: User
# ) -> List[dict]:
#
#     result = await db.execute(
#         select(Medicine).where(
#             Medicine.hospital_id == user.hospital_id,
#             Medicine.branch_id == user.branch_id,
#         )
#     )
#
#     medicines = result.scalars().all()
#
#     stock_status = []
#
#     for med in medicines:
#         if med.stock <= 1:
#             status = "CRITICAL"
#             color = "red"
#             threshold = "1-sheet"
#
#         elif med.stock <= 10:
#             status = "LOW"
#             color = "orange"
#             threshold = "medium"
#
#         else:
#             status = "FULL"
#             color = "green"
#             threshold = "full"
#
#         stock_status.append(
#             {
#                 "id": med.id,
#                 "item_name": med.item_name,
#                 "stock": med.stock,
#                 "status": status,
#                 "color": color,
#                 "threshold": threshold,
#             }
#         )
#
#     return stock_status


async def get_stock_status(
    db: AsyncSession,
    user: User
) -> List[dict]:

    result = await db.execute(
        select(Medicine).where(
            Medicine.hospital_id == user.hospital_id,
            Medicine.branch_id == user.current_branch_id,
        )
    )

    medicines = result.scalars().all()

    stock_status = []

    for med in medicines:

        stock_result = await db.execute(
            select(func.coalesce(func.sum(Batch.quantity_available), 0))
            .where(Batch.medicine_id == med.id)
        )

        stock = stock_result.scalar() or 0

        # Handle NULL/None stock values
        # stock = med.stock if med.stock is not None else 0

        if stock <= 1:
            status = "CRITICAL"
            color = "red"
            threshold = "1-sheet"

        elif stock <= 10:
            status = "LOW"
            color = "orange"
            threshold = "medium"

        else:
            status = "FULL"
            color = "green"
            threshold = "full"

        stock_status.append(
            {
                "id": med.id,
                "item_name": med.item_name or "Unknown Medicine",
                "stock": stock,
                "min_stock": med.min_stock if med.min_stock is not None else 0,
                "status": status,
                "color": color,
                "threshold": threshold,
            }
        )
    return stock_status
