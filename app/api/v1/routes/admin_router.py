from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import async_get_db
from app.models.user_models import ApprovalRequest
from app.models.auth import User
from app.models.entry_models import Medicine
from app.schemas.rolebased_schemas import ShiftOperation, ApprovalDecision, ShiftOperationResponse, ApprovalDecisionOut, \
    ApprovalRequestFullOut, ShiftAssign, ShiftCreate, ShiftOut, PurchaseRequestOut
from app.core.security import require_roles
from app.services.shifts_crud import manage_shift_operations,assign_shift,assign_shift
from app.services.approvals_crud import get_pending_approvals, process_approval_request, get_pending_purchase_requests

router = APIRouter()


@router.post("/shifts/template/{code}", response_model=ShiftOperationResponse)
async def create_shift(
    code: str,
    db: AsyncSession = Depends(async_get_db),
    user=Depends(require_roles(["ADMIN","SUPERADMIN"]))
):
    from app.services.shifts_crud import create_shift_from_template
    return await create_shift_from_template(db, code, user)

# @router.post("/assignshift", response_model=ShiftOperationResponse)
# async def assign_shift(
#     operation: ShiftAssign,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["ADMIN","SUPERADMIN"]))
# ):
#     return await assign_shift_operation(db, operation, current_user)

@router.post("/shifts/assign", response_model=ShiftOperationResponse)
async def assign_shift_route(
    payload: ShiftAssign,
    db: AsyncSession = Depends(async_get_db),
    user = Depends(require_roles(["ADMIN","SUPERADMIN"]))
):
    return await assign_shift(db, payload)


# @router.get("/approvals/pending", response_model=List[ApprovalRequestFullOut])
# async def get_pending_approvals_route(db: AsyncSession = Depends(get_db),user=Depends(role_required(["ADMIN", "SUPERADMIN"]))):
#     return await get_pending_approvals(db)
@router.get("/approvals/pending", response_model=list[ApprovalRequestFullOut])
async def get_pending_approvals_route(
    db: AsyncSession = Depends(async_get_db),
    user=Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    return await get_pending_approvals(db)

@router.get("/purchase-requests/pending", response_model=list[PurchaseRequestOut])
async def get_pending_purchase_requests_route(
    db: AsyncSession = Depends(async_get_db),
    user=Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    return await get_pending_purchase_requests(db)

# @router.post("/approvals/{request_id}/decide", response_model=ApprovalDecisionOut)
# async def decide_approval(request_id: int,decision: ApprovalDecision,db: AsyncSession = Depends(get_db),user=Depends(role_required(["ADMIN", "SUPERADMIN"]))):
#     return await process_approval_request(db, request_id, decision, user)


@router.post(
    "/approvals/{request_id}/decide",
    response_model=ApprovalDecisionOut
)
async def decide_approval(
    request_id: int,
    decision: ApprovalDecision,
    db: AsyncSession = Depends(async_get_db),
    user=Depends(require_roles(["ADMIN", "SUPERADMIN"]))
):
    return await process_approval_request(db, request_id, decision, user)
