# from typing import List
#
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
#
# from app.core.security import async_get_db, require_roles
# from app.models.auth import User
# from app.models.opd import OPDVisit, Prescription
#
# # CRUD
# from app.services.medicine_batch import get_fefo_batch, update_batch_quantity
# from app.services.medicine_entry import get_medicine
# from app.services.non_surgical import (
#     get_fefo_non_surgical_batches,
#     get_non_surgical_item,
#     update_non_surgical_batch_quantity
# )
# from app.services.surgical import (
#     get_fefo_surgical_batch,
#     get_surgical_item,
#     update_surgical_batch_quantity
# )
# from app.services.stock_ledger import create_stock_ledger_entry
#
# # Models
# from app.models.entry_models import PharmacyIssue, Medicine,Batch
#
# # Schemas
# from app.schemas.opdp import (
#     PharmacyIssueCreate,
#     PharmacyIssueResponse
# )
#
# # Utils
# from app.utils.opd import validate_restricted_medicine
# from app.utils.qr_code import generate_qr
#
#
# router = APIRouter(
#     prefix="/opd",
#     tags=["OPD Pharmacy"]
# )
#
#
# # =====================================================
# # ISSUE ITEMS
# # =====================================================
# # @router.post(
# #     "/issue",
# #     response_model=PharmacyIssueResponse,
# #     status_code=status.HTTP_201_CREATED
# # )
# # async def issue_items(
# #     payload: PharmacyIssueCreate,
# #     db: AsyncSession = Depends(get_db)
# # ):
# #
# #     results = []
# #
# #     # ---------------------------------------------
# #     # CREATE ISSUE HEADER
# #     # ---------------------------------------------
# #     issue = PharmacyIssue(
# #         # reference_id=payload.reference_id,
# #         patient_type=payload.patient_type,
# #         prescription_id=payload.prescription_id,
# #         hospital_id=payload.hospital_id,
# #         branch_id=payload.branch_id
# #     )
# #
# #     db.add(issue)
# #     await db.flush()
# #
# #     # ---------------------------------------------
# #     # PROCESS ITEMS
# #     # ---------------------------------------------
# #     for req in payload.items:
# #
# #         item_type = req.item_type
# #         item_id = req.item_id
# #         quantity = req.quantity
# #
# #         # ================= MEDICINE =================
# #         if item_type == "medicine":
# #
# #             item = await get_medicine(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not item:
# #                 raise HTTPException(404, f"Medicine {item_id} not found")
# #
# #             validate_restricted_medicine(item, payload.prescription_id)
# #
# #             batch = await get_fefo_batch(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not batch or batch.quantity_available < quantity:
# #                 raise HTTPException(
# #                     400,
# #                     f"Insufficient stock for {item.item_name}"
# #                 )
# #
# #             new_qty = batch.quantity_available - quantity
# #
# #             await update_batch_quantity(db, batch.id, new_qty)
# #
# #         # ================= SURGICAL =================
# #         elif item_type == "surgical":
# #
# #             item = await get_surgical_item(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not item:
# #                 raise HTTPException(404, "Surgical item not found")
# #
# #             batch = await get_fefo_surgical_batch(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not batch or batch.quantity_available < quantity:
# #                 raise HTTPException(
# #                     400,
# #                     f"Insufficient stock for {item.item_name}"
# #                 )
# #
# #             new_qty = batch.quantity_available - quantity
# #
# #             await update_surgical_batch_quantity(db, batch.id, new_qty)
# #
# #         # ================= NON SURGICAL =================
# #         elif item_type == "non_surgical":
# #
# #             item = await get_non_surgical_item(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not item:
# #                 raise HTTPException(404, "Non-surgical item not found")
# #
# #             batch = await get_fefo_non_surgical_batches(
# #                 db,
# #                 item_id,
# #                 payload.hospital_id,
# #                 payload.branch_id
# #             )
# #
# #             if not batch or batch.quantity_available < quantity:
# #                 raise HTTPException(
# #                     400,
# #                     f"Insufficient stock for {item.item_name}"
# #                 )
# #
# #             new_qty = batch.quantity_available - quantity
# #
# #             await update_non_surgical_batch_quantity(
# #                 db,
# #                 batch.id,
# #                 new_qty
# #             )
# #
# #         else:
# #             raise HTTPException(400, "Invalid item type")
# #
# #         # ---------------------------------------------
# #         # STOCK LEDGER ENTRY
# #         # ---------------------------------------------
# #         await create_stock_ledger_entry(
# #             db=db,
# #             batch_id=batch.id,
# #             batch_type=item_type.upper(),
# #             transaction_type="ISSUE",
# #             quantity_in=0,
# #             quantity_out=quantity,
# #             balance_qty=new_qty,
# #             transaction_value=-quantity * getattr(batch, "cost_price", 0),
# #             reference_id=issue.id,
# #             remarks=f"Issue to {payload.patient_type} #{payload.reference_id}",
# #             hospital_id=payload.hospital_id,
# #             branch_id=payload.branch_id
# #         )
# #
# #         results.append({
# #             "item_type": item_type,
# #             "item_name": item.item_name,
# #             "batch_no": batch.batch_number,
# #             "issued_qty": quantity,
# #             "remaining_qty": new_qty
# #         })
# #
# #     await db.commit()
# #     await db.refresh(issue)
# #
# #     return {
# #         "id": issue.id,
# #         "status": "issued",
# #         "reference_id": payload.reference_id,
# #         "patient_type": payload.patient_type,
# #         "items": results
# #     }
# #
# # @router.post(
# #     "/issue",
# #     response_model=PharmacyIssueResponse,
# #     status_code=status.HTTP_201_CREATED
# # )
# # async def issue_items(
# #     payload: PharmacyIssueCreate,
# #     db: AsyncSession = Depends(async_get_db)
# # ):
# #
# #     results = []
# #     # =====================================
# #     # VALIDATE OPD VISIT
# #     # =====================================
# #     visit_result = await db.execute(
# #         select(OPDVisit).where(
# #             OPDVisit.id == payload.visit_id,
# #             OPDVisit.hospital_id == payload.hospital_id,
# #             OPDVisit.branch_id == payload.branch_id
# #         )
# #     )
# #
# #     visit = visit_result.scalar_one_or_none()
# #
# #     if not visit:
# #         raise HTTPException(
# #             status_code=404,
# #             detail="OPD Visit not found"
# #         )
# #
# #     # =====================================
# #     # VALIDATE PRESCRIPTION BELONGS TO VISIT
# #     # =====================================
# #     prescription_result = await db.execute(
# #         select(Prescription).where(
# #             Prescription.id == payload.prescription_id,
# #             Prescription.visit_id == payload.visit_id
# #         )
# #     )
# #
# #     prescription = prescription_result.scalar_one_or_none()
# #
# #     if not prescription:
# #         raise HTTPException(
# #             status_code=404,
# #             detail="P
# #
# #     # -----------------------------
# #     # CREATE ISSUE HEADER
# #     # -----------------------------
# #     issue = PharmacyIssue(
# #      pharmacy_type=payload.pharmacy_type,
# #         patient_type=payload.patient_type,
# #         visit_id=payload.visit_id,
# #         prescription_id=payload.prescription_id,
# #         patient_name=payload.patient_name,
# #         patient_id_proof=payload.patient_id_proof,
# #         pharmacist_sign=payload.pharmacist_sign,
# #         hospital_id=payload.hospital_id,
# #         branch_id=payload.branch_id,
# #     )
# #
# #     db.add(issue)
# #     await db.flush()
# @router.post(
#     "/issue",
#     response_model=PharmacyIssueResponse,
#     status_code=status.HTTP_201_CREATED
# )
# async def issue_items(
#     payload: PharmacyIssueCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(require_roles("superadmin","pharmacist"))
# ):
#
#     results = []
#
#     # =====================================
#     # VALIDATE OPD VISIT
#     # =====================================
#     visit_result = await db.execute(
#         select(OPDVisit).where(
#             OPDVisit.id == payload.visit_id,
#             OPDVisit.hospital_id == payload.hospital_id,
#             OPDVisit.branch_id == payload.branch_id
#         )
#     )
#
#     visit = visit_result.scalar_one_or_none()
#
#     if not visit:
#         raise HTTPException(
#             status_code=404,
#             detail="OPD Visit not found"
#         )
#
#     # =====================================
#     # VALIDATE PRESCRIPTION BELONGS TO VISIT
#     # =====================================
#     prescription_result = await db.execute(
#         select(Prescription).where(
#             Prescription.id == payload.prescription_id,
#             Prescription.visit_id == payload.visit_id
#         )
#     )
#
#     prescription = prescription_result.scalar_one_or_none()
#
#     if not prescription:
#         raise HTTPException(
#             status_code=404,
#             detail="Prescription not found for this visit"
#         )
#
#     # =====================================
#     # CREATE ISSUE HEADER
#     # =====================================
#     issue = PharmacyIssue(
#         pharmacy_type=payload.pharmacy_type,
#         patient_type=payload.patient_type,
#
#         visit_id=payload.visit_id,               # mapped
#         prescription_id=payload.prescription_id, # mapped
#         item_type=payload.item_type,
#         item_id=payload.item_id,
#         batch_id=payload.batch_id,
#         batch_type=payload.batch_type,
#         patient_name=payload.patient_name,
#         patient_id_proof=payload.patient_id_proof,
#         pharmacist_sign=payload.pharmacist_sign,
#
#         hospital_id=payload.hospital_id,
#         branch_id=payload.branch_id,
#     )
#
#     db.add(issue)
#     await db.flush()
#
#
#     # -----------------------------
#     # PROCESS ITEMS
#     # -----------------------------
#     for req in payload.items:
#
#         item_type = req.item_type
#         item_id = int(req.item_id)
#         quantity = int(req.quantity)
#
#         batch = None
#         new_qty = 0
#
#         # ================= MEDICINE (FEFO BATCH ONLY) =================
#         if item_type == "medicine":
#
#             batch = await get_fefo_batch(
#                 db=db,
#                 hospital_id=payload.hospital_id,
#                 branch_id=payload.branch_id,
#                 medicine_id=item_id,
#                 required_qty=quantity
#             )
#
#             if not batch:
#                 raise HTTPException(
#                     status_code=400,
#                     detail=f"No stock available for medicine_id {item_id}"
#                 )
#
#             if batch.quantity_available < quantity:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Insufficient stock in batch"
#                 )
#
#             new_qty = batch.quantity_available - quantity
#             await update_batch_quantity(
#                 db=db,
#                 hospital_id=payload.hospital_id,
#                 branch_id=payload.branch_id,
#                 batch_id=batch.id,
#                 new_qty=new_qty
#             )
#
#             item_name = getattr(batch, "medicine_name", f"MED-{item_id}")
#
#         # ================= SURGICAL =================
#         elif item_type == "surgical":
#
#             item = await get_surgical_item(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Surgical item not found")
#
#             batch = await get_fefo_surgical_batch(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not batch:
#                 raise HTTPException(400, "No stock available")
#
#             if batch.quantity_available < quantity:
#                 raise HTTPException(400, "Insufficient stock")
#
#             new_qty = batch.quantity_available - quantity
#             await update_surgical_batch_quantity(db, batch.id, new_qty)
#
#             item_name = item.item_name
#
#         # ================= NON SURGICAL =================
#         elif item_type == "non_surgical":
#
#             item = await get_non_surgical_item(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Non-surgical item not found")
#
#             batch = await get_fefo_non_surgical_batches(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not batch:
#                 raise HTTPException(400, "No stock available")
#
#             if batch.quantity_available < quantity:
#                 raise HTTPException(400, "Insufficient stock")
#
#             new_qty = batch.quantity_available - quantity
#             await update_non_surgical_batch_quantity(db, batch.id, new_qty)
#
#             item_name = item.item_name
#
#         else:
#             raise HTTPException(400, "Invalid item type")
#
#         # -----------------------------
#         # SAFETY CHECK
#         # -----------------------------
#         if batch is None:
#             raise HTTPException(400, "Batch not found")
#
#         # -----------------------------
#         # STOCK LEDGER ENTRY
#         # -----------------------------
#         await create_stock_ledger_entry(
#             db=db,
#             batch_id=batch.id,
#             batch_type=item_type.upper(),
#             transaction_type="ISSUE",
#             quantity_in=0,
#             quantity_out=quantity,
#             balance_qty=new_qty,
#             transaction_value=-quantity * getattr(batch, "cost_price", 0),
#             reference_id=issue.id,
#             remarks=f"Issue to {payload.patient_type}",
#             hospital_id=payload.hospital_id,
#             branch_id=payload.branch_id,
#         )
#
#         results.append({
#             "item_type": item_type,
#             "item_name": item_name,
#             "batch_no": getattr(batch, "batch_number", None),
#             "issued_qty": quantity,
#             "remaining_qty": new_qty
#         })
#
#     await db.commit()
#
#     return {
#         "id": issue.id,
#         "status": "issued",
#         "reference_id": issue.id,
#         "patient_type": payload.patient_type,
#         "items": results
#     }
# # =====================================================
# # GET SINGLE ISSUE
# # =====================================================
# # @router.get("/issue/{issue_id}", response_model=PharmacyIssueResponse)
# # async def get_issue(issue_id: int, db: AsyncSession = Depends(get_db)):
# #
# #     result = await db.execute(
# #         select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
# #     )
# #
# #     issue = result.scalar_one_or_none()
# #
# #     if not issue:
# #         raise HTTPException(status_code=404, detail="Issue record not found")
# #
# #     return PharmacyIssueResponse(
# #         id=issue.id,
# #         status="issued",
# #         reference_id=issue.id,
# #         patient_type=issue.patient_type,
# #
# #         # IMPORTANT: you must rebuild items from JSON or related tables
# #         items=[]
# #     )
#
# @router.get("/issue/{issue_id}", response_model=PharmacyIssueResponse)
# @router.get("/issue/{issue_id}", response_model=PharmacyIssueResponse)
# async def get_issue(
#     issue_id: int,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(require_roles("superadmin","pharamacist"))
# ):
#     # -------------------------
#     # GET ISSUE
#     # -------------------------
#     result = await db.execute(
#         select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
#     )
#
#     issue = result.scalar_one_or_none()
#
#     if not issue:
#         raise HTTPException(status_code=404, detail="Issue record not found")
#
#     # -------------------------
#     # GET BATCH (FOR ITEM DETAILS)
#     # -------------------------
#     batch = None
#     item_name = "Unknown"
#
#     if issue.batch_id:
#         batch_result = await db.execute(
#             select(Batch).where(Batch.id == issue.batch_id)
#         )
#         batch = batch_result.scalar_one_or_none()
#
#         if batch and batch.medicine:
#             item_name = batch.medicine.item_name
#
#     # -------------------------
#     # BUILD ITEMS
#     # -------------------------
#     items = []
#
#     if batch:
#         items.append({
#             "item_type": issue.item_type,
#             "item_name": item_name,
#             "batch_no": batch.batch_number,
#             "issued_qty": issue.quantity,
#             "remaining_qty": batch.quantity_available
#         })
#
#     # -------------------------
#     # RESPONSE
#     # -------------------------
#     return PharmacyIssueResponse(
#         id=issue.id,
#         status="issued",
#         reference_id=issue.reference_id or issue.id,
#         patient_type=issue.patient_type,
#         items=items
#     )
# # =====================================================
# # LIST ISSUES
# # =====================================================
# @router.get("/issues", response_model=List[PharmacyIssueResponse])
# async def list_issues(
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(require_roles("superadmin","pharmacist"))
# ):
#     result = await db.execute(select(PharmacyIssue))
#     issues = result.scalars().all()
#
#     response = []
#
#     for issue in issues:
#         response.append(
#             PharmacyIssueResponse(
#                 id=issue.id,
#                 status="issued",
#                 reference_id=issue.reference_id or issue.id,
#                 patient_type=issue.patient_type,
#                 items=issue.medicines_json or []
#             )
#         )
#
#     return response
#
#
# # =====================================================
# # DELETE ISSUE
# # =====================================================
# @router.delete(
#     "/issue/{issue_id}",
#     status_code=status.HTTP_204_NO_CONTENT
# )
# async def delete_issue(
#     issue_id: int,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(require_roles("superadmin","pharmacist"))
# ):
#     result = await db.execute(
#         select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
#     )
#     issue = result.scalar_one_or_none()
#
#     if not issue:
#         raise HTTPException(404, "Issue record not found")
#
#     await db.delete(issue)
#     await db.commit()
#
#
# # =====================================================
# # QR FOR DOCS
# # =====================================================
# @router.get("/qr")
# async def medicine_docs_qr(
#     current_user: User = Depends(require_roles("superadmin","pharmacist","doctor"))
# ):
#     url = "http://localhost:8000/docs#/OPD%20Pharmacy"
#     return generate_qr(url)

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import async_get_db, require_roles
from app.models.auth import User
from app.models.opd import OPDVisit, Prescription

# CRUD
from app.services.medicine_batch import get_fefo_batch, update_batch_quantity
from app.services.medicine_entry import get_medicine
from app.services.non_surgical import (
    get_fefo_non_surgical_batches,
    get_non_surgical_item,
    update_non_surgical_batch_quantity
)
from app.services.surgical import (
    get_fefo_surgical_batch,
    get_surgical_item,
    update_surgical_batch_quantity
)
from app.services.stock_ledger import create_stock_ledger_entry

# Models
from app.models.entry_models import PharmacyIssue, Medicine,Batch

# Schemas
from app.schemas.opdp import (
    PharmacyIssueCreate,
    PharmacyIssueResponse
)

# Utils
from app.utils.opd import validate_restricted_medicine
from app.utils.qr_code import generate_qr


router = APIRouter(
    prefix="/opd",
    tags=["OPD Pharmacy"]
)


# =====================================================
# ISSUE ITEMS
# =====================================================
# @router.post(
#     "/issue",
#     response_model=PharmacyIssueResponse,
#     status_code=status.HTTP_201_CREATED
# )
# async def issue_items(
#     payload: PharmacyIssueCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#
#     results = []
#
#     # ---------------------------------------------
#     # CREATE ISSUE HEADER
#     # ---------------------------------------------
#     issue = PharmacyIssue(
#         # reference_id=payload.reference_id,
#         patient_type=payload.patient_type,
#         prescription_id=payload.prescription_id,
#         hospital_id=payload.hospital_id,
#         branch_id=payload.branch_id
#     )
#
#     db.add(issue)
#     await db.flush()
#
#     # ---------------------------------------------
#     # PROCESS ITEMS
#     # ---------------------------------------------
#     for req in payload.items:
#
#         item_type = req.item_type
#         item_id = req.item_id
#         quantity = req.quantity
#
#         # ================= MEDICINE =================
#         if item_type == "medicine":
#
#             item = await get_medicine(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, f"Medicine {item_id} not found")
#
#             validate_restricted_medicine(item, payload.prescription_id)
#
#             batch = await get_fefo_batch(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
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
#             await update_batch_quantity(db, batch.id, new_qty)
#
#         # ================= SURGICAL =================
#         elif item_type == "surgical":
#
#             item = await get_surgical_item(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Surgical item not found")
#
#             batch = await get_fefo_surgical_batch(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
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
#             await update_surgical_batch_quantity(db, batch.id, new_qty)
#
#         # ================= NON SURGICAL =================
#         elif item_type == "non_surgical":
#
#             item = await get_non_surgical_item(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
#             )
#
#             if not item:
#                 raise HTTPException(404, "Non-surgical item not found")
#
#             batch = await get_fefo_non_surgical_batches(
#                 db,
#                 item_id,
#                 payload.hospital_id,
#                 payload.branch_id
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
#         else:
#             raise HTTPException(400, "Invalid item type")
#
#         # ---------------------------------------------
#         # STOCK LEDGER ENTRY
#         # ---------------------------------------------
#         await create_stock_ledger_entry(
#             db=db,
#             batch_id=batch.id,
#             batch_type=item_type.upper(),
#             transaction_type="ISSUE",
#             quantity_in=0,
#             quantity_out=quantity,
#             balance_qty=new_qty,
#             transaction_value=-quantity * getattr(batch, "cost_price", 0),
#             reference_id=issue.id,
#             remarks=f"Issue to {payload.patient_type} #{payload.reference_id}",
#             hospital_id=payload.hospital_id,
#             branch_id=payload.branch_id
#         )
#
#         results.append({
#             "item_type": item_type,
#             "item_name": item.item_name,
#             "batch_no": batch.batch_number,
#             "issued_qty": quantity,
#             "remaining_qty": new_qty
#         })
#
#     await db.commit()
#     await db.refresh(issue)
#
#     return {
#         "id": issue.id,
#         "status": "issued",
#         "reference_id": payload.reference_id,
#         "patient_type": payload.patient_type,
#         "items": results
#     }
#
# @router.post(
#     "/issue",
#     response_model=PharmacyIssueResponse,
#     status_code=status.HTTP_201_CREATED
# )
# async def issue_items(
#     payload: PharmacyIssueCreate,
#     db: AsyncSession = Depends(async_get_db)
# ):
#
#     results = []
#     # =====================================
#     # VALIDATE OPD VISIT
#     # =====================================
#     visit_result = await db.execute(
#         select(OPDVisit).where(
#             OPDVisit.id == payload.visit_id,
#             OPDVisit.hospital_id == payload.hospital_id,
#             OPDVisit.branch_id == payload.branch_id
#         )
#     )
#
#     visit = visit_result.scalar_one_or_none()
#
#     if not visit:
#         raise HTTPException(
#             status_code=404,
#             detail="OPD Visit not found"
#         )
#
#     # =====================================
#     # VALIDATE PRESCRIPTION BELONGS TO VISIT
#     # =====================================
#     prescription_result = await db.execute(
#         select(Prescription).where(
#             Prescription.id == payload.prescription_id,
#             Prescription.visit_id == payload.visit_id
#         )
#     )
#
#     prescription = prescription_result.scalar_one_or_none()
#
#     if not prescription:
#         raise HTTPException(
#             status_code=404,
#             detail="P
#
#     # -----------------------------
#     # CREATE ISSUE HEADER
#     # -----------------------------
#     issue = PharmacyIssue(
#      pharmacy_type=payload.pharmacy_type,
#         patient_type=payload.patient_type,
#         visit_id=payload.visit_id,
#         prescription_id=payload.prescription_id,
#         patient_name=payload.patient_name,
#         patient_id_proof=payload.patient_id_proof,
#         pharmacist_sign=payload.pharmacist_sign,
#         hospital_id=payload.hospital_id,
#         branch_id=payload.branch_id,
#     )
#
#     db.add(issue)
#     await db.flush()
@router.post(
    "/issue",
    response_model=PharmacyIssueResponse,
    status_code=status.HTTP_201_CREATED
)
async def issue_items(
    payload: PharmacyIssueCreate,
    db: AsyncSession = Depends(async_get_db),
    pharmacist: User = Depends(require_roles("pharmacist","superadmin")),
):

    results = []

    # =====================================
    # VALIDATE OPD VISIT
    # =====================================
    visit_result = await db.execute(
        select(OPDVisit).where(
            OPDVisit.id == payload.visit_id,
            OPDVisit.hospital_id == payload.hospital_id,
            OPDVisit.branch_id == payload.branch_id
        )
    )

    visit = visit_result.scalar_one_or_none()

    if not visit:
        raise HTTPException(
            status_code=404,
            detail="OPD Visit not found"
        )

    # =====================================
    # VALIDATE PRESCRIPTION BELONGS TO VISIT
    # =====================================
    prescription_result = await db.execute(
        select(Prescription).where(
            Prescription.id == payload.prescription_id,
            Prescription.visit_id == payload.visit_id
        )
    )

    prescription = prescription_result.scalar_one_or_none()

    if not prescription:
        raise HTTPException(
            status_code=404,
            detail="Prescription not found for this visit"
        )

    # =====================================
    # CREATE ISSUE HEADER
    # =====================================
    # issue = PharmacyIssue(
    #     pharmacy_type=payload.pharmacy_type,
    #     patient_type=payload.patient_type,
    #
    #     visit_id=payload.visit_id,
    #     prescription_id=payload.prescription_id,
    #     item_type=payload.item_type,
    #     # item_id=payload.item_id,
    #     # batch_id=payload.batch_id,
    #     # batch_type=payload.batch_type,
    #     patient_name=payload.patient_name,
    #     patient_id_proof=payload.patient_id_proof,
    #     pharmacist_sign=payload.pharmacist_sign,
    #
    #
    #     hospital_id=payload.hospital_id,
    #     branch_id=payload.branch_id,
    # )
    issue = PharmacyIssue(
        pharmacy_type=payload.pharmacy_type,
        patient_type=payload.patient_type,
        visit_id=payload.visit_id,
        prescription_id=payload.prescription_id,

        item_type=payload.item_type,
        item_id=payload.item_id,
        batch_id=payload.batch_id,
        batch_type=payload.batch_type,
        # quantity=payload.quantity,

        patient_name=payload.patient_name,
        patient_id_proof=payload.patient_id_proof,
        pharmacist_sign=payload.pharmacist_sign,

        hospital_id=payload.hospital_id,
        branch_id=payload.branch_id,
    )

    db.add(issue)
    await db.flush()


    # -----------------------------
    # PROCESS ITEMS
    # -----------------------------
    for req in payload.items:

        item_type = req.item_type
        item_id = int(req.item_id)
        quantity = int(req.quantity)

        batch = None
        new_qty = 0

        # ================= MEDICINE (FEFO BATCH ONLY) =================
        if item_type == "medicine":

            batch = await get_fefo_batch(
                db=db,
                hospital_id=payload.hospital_id,
                branch_id=payload.branch_id,
                medicine_id=item_id,
                required_qty=quantity
            )

            if not batch:
                raise HTTPException(
                    status_code=400,
                    detail=f"No stock available for medicine_id {item_id}"
                )

            if batch.quantity_available < quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock in batch"
                )

            new_qty = batch.quantity_available - quantity
            await update_batch_quantity(
                db=db,
                hospital_id=payload.hospital_id,
                branch_id=payload.branch_id,
                batch_id=batch.id,
                new_qty=new_qty
            )

            item_name = getattr(batch, "medicine_name", f"MED-{item_id}")

        # ================= SURGICAL =================
        elif item_type == "surgical":

            item = await get_surgical_item(
                db,
                item_id,
                payload.hospital_id,
                payload.branch_id
            )

            if not item:
                raise HTTPException(404, "Surgical item not found")

            batch = await get_fefo_surgical_batch(
                db,
                item_id,
                payload.hospital_id,
                payload.branch_id
            )

            if not batch:
                raise HTTPException(400, "No stock available")

            if batch.quantity_available < quantity:
                raise HTTPException(400, "Insufficient stock")

            new_qty = batch.quantity_available - quantity
            await update_surgical_batch_quantity(db, batch.id, new_qty)

            item_name = item.item_name

        # ================= NON SURGICAL =================
        elif item_type == "non_surgical":

            item = await get_non_surgical_item(
                db,
                item_id,
                payload.hospital_id,
                payload.branch_id
            )

            if not item:
                raise HTTPException(404, "Non-surgical item not found")

            batch = await get_fefo_non_surgical_batches(
                db,
                item_id,
                payload.hospital_id,
                payload.branch_id
            )

            if not batch:
                raise HTTPException(400, "No stock available")

            if batch.quantity_available < quantity:
                raise HTTPException(400, "Insufficient stock")

            new_qty = batch.quantity_available - quantity
            await update_non_surgical_batch_quantity(db, batch.id, new_qty)

            item_name = item.item_name

        else:
            raise HTTPException(400, "Invalid item type")

        # -----------------------------
        # SAFETY CHECK
        # -----------------------------
        if batch is None:
            raise HTTPException(400, "Batch not found")

        # -----------------------------
        # STOCK LEDGER ENTRY
        # -----------------------------
        await create_stock_ledger_entry(
            db=db,
            batch_id=batch.id,
            batch_type=item_type.upper(),
            transaction_type="ISSUE",
            quantity_in=0,
            quantity_out=quantity,
            balance_qty=new_qty,
            transaction_value=-quantity * getattr(batch, "cost_price", 0),
            reference_id=issue.id,
            remarks=f"Issue to {payload.patient_type}",
            hospital_id=payload.hospital_id,
            branch_id=payload.branch_id,
        )

        results.append({
            "item_type": item_type,
            "item_name": item_name,
            "batch_no": getattr(batch, "batch_number", None),
            "issued_qty": quantity,
            "remaining_qty": new_qty
        })

    await db.commit()

    return {
        "id": issue.id,
        "status": "issued",
        "reference_id": issue.id,
        "patient_type": payload.patient_type,
        "items": results
    }
# =====================================================
# GET SINGLE ISSUE
# =====================================================
# @router.get("/issue/{issue_id}", response_model=PharmacyIssueResponse)
# async def get_issue(issue_id: int, db: AsyncSession = Depends(get_db)):
#
#     result = await db.execute(
#         select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
#     )
#
#     issue = result.scalar_one_or_none()
#
#     if not issue:
#         raise HTTPException(status_code=404, detail="Issue record not found")
#
#     return PharmacyIssueResponse(
#         id=issue.id,
#         status="issued",
#         reference_id=issue.id,
#         patient_type=issue.patient_type,
#
#         # IMPORTANT: you must rebuild items from JSON or related tables
#         items=[]
#     )

@router.get("/issue/{issue_id}", response_model=PharmacyIssueResponse)
async def get_issue(issue_id: int, db: AsyncSession = Depends(async_get_db),pharmacist: User = Depends(require_roles("pharmacist","superadmin")),):

    # -------------------------
    # GET ISSUE
    # -------------------------
    result = await db.execute(
        select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
    )

    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue record not found")

    # -------------------------
    # GET BATCH (FOR ITEM DETAILS)
    # -------------------------
    batch = None
    item_name = "Unknown"

    if issue.batch_id:
        batch_result = await db.execute(
            select(Batch).where(Batch.id == issue.batch_id)
        )
        batch = batch_result.scalar_one_or_none()

        if batch and batch.medicine:
            item_name = batch.medicine.item_name

    # -------------------------
    # BUILD ITEMS
    # -------------------------
    items = []

    if batch:
        items.append({
            "item_type": issue.item_type,
            "item_name": item_name,
            "batch_no": batch.batch_number,
            "issued_qty": issue.quantity,
            "remaining_qty": batch.quantity_available
        })

    # -------------------------
    # RESPONSE
    # -------------------------
    return PharmacyIssueResponse(
        id=issue.id,
        status="issued",
        reference_id=issue.reference_id or issue.id,
        patient_type=issue.patient_type,
        items=items
    )
# =====================================================
# LIST ISSUES
# =====================================================
@router.get("/issues", response_model=List[PharmacyIssueResponse])
async def list_issues(db: AsyncSession = Depends(async_get_db),pharmacist: User = Depends(require_roles("pharmacist","superadmin")),):

    result = await db.execute(select(PharmacyIssue))
    issues = result.scalars().all()

    response = []

    for issue in issues:
        response.append(
            PharmacyIssueResponse(
                id=issue.id,
                status="issued",
                reference_id=issue.reference_id or issue.id,
                patient_type=issue.patient_type,
                items=issue.medicines_json or []
            )
        )

    return response


# =====================================================
# DELETE ISSUE
# =====================================================
@router.delete(
    "/issue/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_issue(issue_id: int, db: AsyncSession = Depends(async_get_db),pharmacist: User = Depends(require_roles("pharmacist","superadmin")),):

    result = await db.execute(
        select(PharmacyIssue).where(PharmacyIssue.id == issue_id)
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(404, "Issue record not found")

    await db.delete(issue)
    await db.commit()
    return {"message:opd issue deleted successfully"}


# =====================================================
# QR FOR DOCS
# =====================================================
@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/OPD%20Pharmacy"
    return generate_qr(url)