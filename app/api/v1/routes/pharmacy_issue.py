
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, datetime, time, timedelta
from typing import List, Optional
# what does this line say exactly?
from app.services.medicine_entry import get_fefo_batch


from app.core.security import async_get_db
from app.models.auth import User
from app.core.security import require_roles

from app.schemas.entry_schemas import (
    PharmacyIssueRead,
    IssueRequest,
    IssueItemLine,
    StockLedgerRead
)

from app.models.entry_models import NonSurgicalBatch, StockLedger, Batch, SurgicalBatch

from app.services.medicine_entry import get_medicine
from app.services.medicine_batch import get_fefo_batch, update_batch_quantity
from app.services.surgical import (
    get_surgical_item,
    get_fefo_surgical_batch,
    update_surgical_batch_quantity
)
from app.services.non_surgical import (
    get_non_surgical_item,
    get_fefo_non_surgical_batches,
    update_non_surgical_batch_quantity
)

from app.services.stock_ledger import create_stock_ledger_entry
from app.services.pharmacy_issue import (
    create_pharmacy_issue,
    get_pharmacy_issue,
    list_pharmacy_issues,
    cancel_pharmacy_issue
)
from app.services.medicine_entry import get_fefo_batch



router = APIRouter(prefix="/pharmacy-issue", tags=["pharmacy issue"])

#
# @router.post("/issue")
# async def issue_items(
#     payload: IssueRequest,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(role_required(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
# ):
#
#     results = []
#
#     hospital_id = user.hospital_id
#     branch_id = user.branch_id
#
#     for req in payload.items:
#
#         item_type = req.item_type
#         item_id = req.item_id
#         quantity = req.quantity
#
#         # ==========================
#         # MEDICINE
#         # ==========================
#         if item_type == "medicine":
#
#             item = await get_medicine(
#                 db,
#                 item_id,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Medicine not found")
#
#             batch = await get_fefo_batch(
#                 db,
#                 item_id,
#                 quantity,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not batch or batch.quantity_available < quantity:
#                 raise HTTPException(
#                     400,
#                     f"Insufficient stock for {item.item_name}"
#                 )
#
#             new_qty = batch.quantity_available - quantity
#
#             await update_batch_quantity(
#                 db,
#                 batch.id,
#                 new_qty
#             )
#
#             await create_pharmacy_issue(
#                 db=db,
#                 hospital_id=hospital_id,
#                 branch_id=branch_id,
#                 item_type="medicine",
#                 item_id=item.id,
#                 batch_type="medicine",
#                 batch_id=batch.id,
#                 patient_type=payload.patient_type,
#                 reference_id=payload.reference_id,
#                 quantity=quantity,
#                 rate_per_unit=batch.cost_price,
#                 issue_value=quantity * batch.cost_price,
#                 issued_by=user.username
#             )
#
#             await create_stock_ledger_entry(
#                 db,
#                 batch.id,
#                 "medicine",
#                 "ISSUE",
#                 0,
#                 quantity,
#                 new_qty,
#                 -(quantity * batch.cost_price),
#                 f"Issue to {payload.patient_type} #{payload.reference_id}",
#                 hospital_id,
#                 branch_id
#             )
#
#             results.append({
#                 "item_type": "medicine",
#                 "item_name": item.item_name,
#                 "batch_no": batch.batch_number,
#                 "issued_qty": quantity,
#                 "remaining_qty": new_qty
#             })
#
#         # ==========================
#         # SURGICAL
#         # ==========================
#         elif item_type == "surgical":
#
#             item = await get_surgical_item(
#                 db,
#                 item_id,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Surgical item not found")
#
#             batch = await get_fefo_surgical_batch(
#                 db,
#                 item_id,
#                 quantity,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not batch or batch.quantity_available < quantity:
#                 raise HTTPException(
#                     400,
#                     f"Insufficient stock for {item.item_name}"
#                 )
#
#             new_qty = batch.quantity_available - quantity
#
#             await update_surgical_batch_quantity(
#                 db,
#                 batch.id,
#                 new_qty
#             )
#
#             await create_pharmacy_issue(
#                 db=db,
#                 hospital_id=hospital_id,
#                 branch_id=branch_id,
#                 item_type="surgical",
#                 item_id=item.id,
#                 batch_type="surgical",
#                 batch_id=batch.id,
#                 patient_type=payload.patient_type,
#                 reference_id=payload.reference_id,
#                 quantity=quantity,
#                 rate_per_unit=batch.cost_price,
#                 issue_value=quantity * batch.cost_price,
#                 issued_by=user.username
#             )
#
#             await create_stock_ledger_entry(
#                 db,
#                 batch.id,
#                 "surgical",
#                 "ISSUE",
#                 0,
#                 quantity,
#                 new_qty,
#                 -(quantity * batch.cost_price),
#                 f"Issue to {payload.patient_type} #{payload.reference_id}",
#                 hospital_id,
#                 branch_id
#             )
#
#             results.append({
#                 "item_type": "surgical",
#                 "item_name": item.item_name,
#                 "batch_no": batch.batch_number,
#                 "issued_qty": quantity,
#                 "remaining_qty": new_qty
#             })
#
#         # ==========================
#         # NON SURGICAL
#         # ==========================
#         elif item_type == "non_surgical":
#
#             item = await get_non_surgical_item(
#                 db,
#                 item_id,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Non surgical item not found")
#
#             batch = await get_fefo_non_surgical_batches(
#                 db,
#                 item_id,
#                 quantity,
#                 hospital_id,
#                 branch_id
#             )
#
#             if not batch or batch.quantity_available < quantity:
#                 raise HTTPException(
#                     400,
#                     f"Insufficient stock for {item.item_name}"
#                 )
#
#             new_qty = batch.quantity_available - quantity
#
#             await update_non_surgical_batch_quantity(
#                 db,
#                 batch.id,
#                 new_qty
#             )
#
#             await create_pharmacy_issue(
#                 db=db,
#                 hospital_id=hospital_id,
#                 branch_id=branch_id,
#                 item_type="non_surgical",
#                 item_id=item.id,
#                 batch_type="non_surgical",
#                 batch_id=batch.id,
#                 patient_type=payload.patient_type,
#                 reference_id=payload.reference_id,
#                 quantity=quantity,
#                 rate_per_unit=batch.cost_price,
#                 issue_value=quantity * batch.cost_price,
#                 issued_by=user.username
#             )
#
#             await create_stock_ledger_entry(
#                 db,
#                 batch.id,
#                 "non_surgical",
#                 "ISSUE",
#                 0,
#                 quantity,
#                 new_qty,
#                 -(quantity * batch.cost_price),
#                 f"Issue to {payload.patient_type} #{payload.reference_id}",
#                 hospital_id,
#                 branch_id
#             )
#
#             results.append({
#                 "item_type": "non_surgical",
#                 "item_name": item.item_name,
#                 "batch_no": batch.batch_number,
#                 "issued_qty": quantity,
#                 "remaining_qty": new_qty
#             })
#
#     await db.commit()
#
#     return {
#         "status": "issued",
#         "reference_id": payload.reference_id,
#         "patient_type": payload.patient_type,
#         "items": results
#     }

@router.post("/issue")
async def issue_items(
    payload: IssueRequest,
    db: AsyncSession = Depends(async_get_db),
    user: User = Depends(require_roles(["PHARMACIST", "ADMIN", "SUPERADMIN"]))
):
    results = []
    hospital_id = user.hospital_id
    branch_id = user.current_branch_id

    for req in payload.items:
        item_type = req.item_type
        item_id = req.item_id
        quantity = req.quantity

        # ==========================
        # MEDICINE
        # ==========================
        if item_type == "medicine":

            item = await get_medicine(db, item_id, hospital_id, branch_id)
            if not item:
                raise HTTPException(404, "Medicine not found")

            batch = await get_fefo_batch(
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                medicine_id=item_id,
                required_qty=quantity
            )
            if not batch or batch.quantity_available < quantity:
                raise HTTPException(400, f"Insufficient stock for {item.item_name}")

            new_qty = batch.quantity_available - quantity
            await update_batch_quantity(
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                batch_id=batch.id,
                new_qty=new_qty
            )

            await create_pharmacy_issue(
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                item_type="medicine",
                item_id=item.id,
                batch_type="medicine",
                batch_id=batch.id,
                patient_type=payload.patient_type,
                reference_id=payload.reference_id,
                quantity=quantity,
                rate_per_unit=batch.cost_price,
                issue_value=quantity * batch.cost_price,
                issued_by=user.username,
                pharmacist_id=int(user.id)
            )

            await create_stock_ledger_entry(  #  fixed keyword args
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                batch_id=batch.id,
                batch_type="medicine",
                transaction_type="ISSUE",
                quantity_in=0,
                quantity_out=quantity,
                balance_qty=new_qty,
                transaction_value=quantity * batch.cost_price,
                reference_id=payload.reference_id,
                remarks=f"Issue to {payload.patient_type} #{payload.reference_id}",
            )

            results.append({
                "item_type": "medicine",
                "item_name": item.item_name,
                "batch_no": batch.batch_number,
                "issued_qty": quantity,
                "remaining_qty": new_qty,
            })

        # ==========================
        # SURGICAL
        # ==========================
        elif item_type == "surgical":

            item = await get_surgical_item(db, item_id, hospital_id, branch_id)
            if not item:
                raise HTTPException(404, "Surgical item not found")

            batch = await get_fefo_surgical_batch(db, item_id, quantity, hospital_id, branch_id)
            if not batch or batch.quantity_available < quantity:
                raise HTTPException(400, f"Insufficient stock for {item.item_name}")

            new_qty = batch.quantity_available - quantity
            await update_surgical_batch_quantity(db, batch.id, new_qty)

            await create_pharmacy_issue(
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                item_type="surgical",
                item_id=item.id,
                batch_type="surgical",
                batch_id=batch.id,
                patient_type=payload.patient_type,
                reference_id=payload.reference_id,
                quantity=quantity,
                rate_per_unit=batch.cost_price,
                issue_value=quantity * batch.cost_price,
                issued_by=user.username,
                pharmacist_id=int(user.id)
            )

            await create_stock_ledger_entry(  #  fixed keyword args
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                batch_id=batch.id,
                batch_type="surgical",
                transaction_type="ISSUE",
                quantity_in=0,
                quantity_out=quantity,
                balance_qty=new_qty,
                transaction_value=quantity * batch.cost_price,
                reference_id=payload.reference_id,
                remarks=f"Issue to {payload.patient_type} #{payload.reference_id}",
            )

            results.append({
                "item_type": "surgical",
                "item_name": item.item_name,
                "batch_no": batch.batch_number,
                "issued_qty": quantity,
                "remaining_qty": new_qty,
            })

        # ==========================
        # NON SURGICAL
        # ==========================
        elif item_type == "non_surgical":

            item = await get_non_surgical_item(db, item_id, hospital_id, branch_id)
            if not item:
                raise HTTPException(404, "Non surgical item not found")

            batch = await get_fefo_non_surgical_batches(db, item_id, quantity, hospital_id, branch_id)
            if not batch or batch.quantity_available < quantity:
                raise HTTPException(400, f"Insufficient stock for {item.item_name}")

            new_qty = batch.quantity_available - quantity
            await update_non_surgical_batch_quantity(db, batch.id, new_qty)

            await create_pharmacy_issue(
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                item_type="non_surgical",
                item_id=item.id,
                batch_type="non_surgical",
                batch_id=batch.id,
                patient_type=payload.patient_type,
                reference_id=payload.reference_id,
                quantity=quantity,
                rate_per_unit=batch.cost_price,
                issue_value=quantity * batch.cost_price,
                issued_by=user.username,
                pharmacist_id=int(user.id)
            )

            await create_stock_ledger_entry(  # fixed keyword args
                db=db,
                hospital_id=hospital_id,
                branch_id=branch_id,
                batch_id=batch.id,
                batch_type="non_surgical",
                transaction_type="ISSUE",
                quantity_in=0,
                quantity_out=quantity,
                balance_qty=new_qty,
                transaction_value=quantity * batch.cost_price,
                reference_id=payload.reference_id,
                remarks=f"Issue to {payload.patient_type} #{payload.reference_id}",
            )

            results.append({
                "item_type": "non_surgical",
                "item_name": item.item_name,
                "batch_no": batch.batch_number,
                "issued_qty": quantity,
                "remaining_qty": new_qty,
            })

        else:
            raise HTTPException(400, f"Invalid item_type: {item_type}. Must be medicine, surgical, or non_surgical")

    await db.commit()

    return {
        "status": "issued",
        "reference_id": payload.reference_id,
        "patient_type": payload.patient_type,
        "items": results,
    }

