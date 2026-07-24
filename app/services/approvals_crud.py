from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from datetime import datetime
from app.models.user_models import ApprovalRequest,PurchaseRequest
from app.models.auth import User
from app.models.entry_models import Medicine
from app.schemas.rolebased_schemas import ApprovalDecision

# async def get_pending_approvals(db: AsyncSession):
#     result = await db.execute(
#         select(ApprovalRequest).where(ApprovalRequest.status == "PENDING")
#     )
#     return result.scalars().all()

#
# async def get_pending_approvals(db: AsyncSession):
#     result = await db.execute(
#         select(
#             ApprovalRequest,
#             User.username,
#             Medicine.item_name
#         )
#         .join(User, ApprovalRequest.pharmacist_id == User.id)
#         .join(Medicine, ApprovalRequest.medicine_id == Medicine.id)
#         .where(func.upper(ApprovalRequest.status) == "PENDING")
#     )
#
#     rows = result.all()
#
#     return [
#         {
#             "id": r.ApprovalRequest.id,
#             "pharmacist_id": r.ApprovalRequest.pharmacist_id,
#             "medicine_id": r.ApprovalRequest.medicine_id,
#             "patient_id": r.ApprovalRequest.patient_id,
#             "quantity": r.ApprovalRequest.quantity,
#             "status": r.ApprovalRequest.status,
#             "created_at": r.ApprovalRequest.created_at,
#             "pharmacist_name": r.username,
#             "medicine_name": r.name,
#         }
#         for r in rows
#     ]

async def get_pending_approvals(db: AsyncSession):
    stmt = (
        select(
            ApprovalRequest,
            User.username,
            Medicine.item_name
        )
        .join(User, ApprovalRequest.pharmacist_id == User.id)
        .join(Medicine, ApprovalRequest.medicine_id == Medicine.id)
        .where(ApprovalRequest.status == "PENDING")
    )

    result = await db.execute(stmt)
    rows = result.all()

    output = []
    for approval, pharmacist_name, medicine_name in rows:
        output.append({
            "id": approval.id,
            "pharmacist_id": approval.pharmacist_id,
            "patient_id": approval.patient_id,
            "medicine_id": approval.medicine_id,
            "quantity": approval.quantity,
            "status": approval.status,
            "created_at": approval.created_at,
            "pharmacist_name": pharmacist_name,
            "medicine_name": medicine_name,
        })

    return output

async def get_pending_purchase_requests(db: AsyncSession):
    stmt = (
        select(PurchaseRequest)
        .where(PurchaseRequest.status == "PENDING")
    )

    result = await db.execute(stmt)
    return result.scalars().all()
#
# async def process_approval_request(db: AsyncSession, request_id: int, decision: ApprovalDecision, user):
#     result = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == request_id))
#     request = result.scalar_one_or_none()
#     if not request:
#         raise HTTPException(status_code=404, detail="Approval request not found")
#
#     if request.status != "PENDING":
#         raise HTTPException(status_code=400, detail="Request is not pending")
#
#     if decision.approve:
#         med_result = await db.execute(select(Medicine).where(Medicine.id == request.medicine_id))
#         medicine = med_result.scalar_one_or_none()
#         if not medicine:
#             raise HTTPException(status_code=404, detail="Medicine not found")
#
#         if medicine.stock < request.quantity:
#             raise HTTPException(status_code=400, detail="Insufficient stock for approval")
#
#         medicine.stock -= request.quantity
#         request.status = "APPROVED"
#     else:
#         request.status = "REJECTED"
#
#     request.decided_at = datetime.utcnow()
#     request.manager_id = user.id
#     request.note = decision.note
#
#     await db.commit()
#     await db.refresh(request)
#     return {"message": f"Request {request.status}", "request_id": request.id}



async def process_approval_request(
    db: AsyncSession,
    request_id: int,
    decision,
    user
):


    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == request_id)
    )
    request = result.scalar_one_or_none()

    request_type = "approval"

    if not request:
        result = await db.execute(
            select(PurchaseRequest).where(PurchaseRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        request_type = "purchase"

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Request already processed"
        )

    med_result = await db.execute(
        select(Medicine).where(Medicine.id == request.medicine_id)
    )
    medicine = med_result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")


    if decision.approve:

        # Case A: Enough stock
        if medicine.stock >= request.quantity:
            medicine.stock -= request.quantity
            request.status = "APPROVED"

        # Case B: Not enough stock
        else:
            if user.role in ["ADMIN", "SUPERADMIN"]:
                # Admin override → allow approval but do NOT deduct stock
                request.status = "APPROVED_BACKORDER"
            else:
                # Normal user → block approval
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock"
                )

    else:
        request.status = "REJECTED"


    request.decided_at = datetime.utcnow()
    request.manager_id = user.id
    request.note = decision.note


    await db.commit()
    await db.refresh(request)

    return {
        "message": f"{request_type.upper()} request {request.status}",
        "request_id": request.id,
        "type": request_type,
        "approved": request.status.startswith("APPROVED"),
        "processed_by": user.id,
        "processed_at": request.decided_at,
    }