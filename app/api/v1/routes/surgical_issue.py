# from fastapi import APIRouter, Depends, Form, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database.user_db import get_db
# from app.crud.surgical import get_surgical_item, get_fefo_surgical_batch, update_surgical_batch_quantity
# from app.crud.stock_ledger import create_stock_ledger_entry
# from app.models.models import SurgicalBatch
#
# router = APIRouter(prefix="/surgical-issue", tags=["Surgical Issue"])
#
# @router.post("/")
# async def issue_surgical_item(
#         procedure_id: int = Form(...),
#         surgical_item_id: int = Form(...),
#         quantity: int = Form(...),
#         patient_type: str = Form(...),
#         db: AsyncSession = Depends(get_db)
# ):
#     item = await get_surgical_item(db, surgical_item_id)
#     if not item:
#         raise HTTPException(404, "Surgical item not found")
#
#     batch = await get_fefo_surgical_batch(db, surgical_item_id, quantity)
#     if not batch or batch.quantity_available < quantity:
#         raise HTTPException(400, "Insufficient FEFO stock")
#
#     new_qty = batch.quantity_available - quantity
#     await update_surgical_batch_quantity(db, batch.id, new_qty)
#     await create_stock_ledger_entry(
#         db, batch.id, "ISSUE", 0, quantity, new_qty,
#         -quantity * batch.cost_price, f"Issue to {patient_type} procedureid {procedure_id}"
#     )
#
#     return {
#         "status": "issued",
#         "batch_id": batch.id,
#         "rackshelf": batch.rack_shelf_number,
#         "remaining_qty": new_qty
#     }
