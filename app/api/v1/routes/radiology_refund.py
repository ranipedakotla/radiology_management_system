from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_refund import (
    RefundResponse,
)

from app.services.radiology_refund import (
    RefundService,
)


router = APIRouter(
    prefix="/radiology_refunds",
    tags=["Radiology Refund"]
)



# ========================================
# CREATE REFUND REQUEST
# Role: Receptionist
# ========================================
@router.post(
    "/",
    response_model=RefundResponse,
    status_code=201
)
def create_refund_request(

    registration_id: int = Form(...),

    cancellation_reason: str = Form(...),

    refund_amount: float = Form(...),

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.create_refund_request(

        registration_id=registration_id,

        cancellation_reason=cancellation_reason,

        refund_amount=refund_amount
    )



# ========================================
# APPROVE REFUND
# Role: Admin / Account Manager
# ========================================
@router.put(
    "/{refund_id}/approve",
    response_model=RefundResponse
)
def approve_refund(

    refund_id: int,

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.approve_refund(
        refund_id
    )



# ========================================
# REJECT REFUND
# Role: Admin / Account Manager
# ========================================
@router.put(
    "/{refund_id}/reject",
    response_model=RefundResponse
)
def reject_refund(

    refund_id: int,

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.reject_refund(
        refund_id
    )



# ========================================
# PROCESS REFUND
# Role: Billing Executive
# ========================================
@router.put(
    "/{refund_id}/process",
    response_model=RefundResponse
)
def process_refund(

    refund_id: int,

    refund_mode: str = Form(...),

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.process_refund(

        refund_id=refund_id,

        refund_mode=refund_mode
    )



# ========================================
# GET ALL REFUNDS
# ========================================
@router.get(
    "/",
    response_model=list[
        RefundResponse
    ]
)
def get_all_refunds(

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.get_all_refunds()



# ========================================
# GET REFUND BY ID
# ========================================
@router.get(
    "/{refund_id}",
    response_model=RefundResponse
)
def get_refund(

    refund_id: int,

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.get_refund(
        refund_id
    )



# ========================================
# DELETE REFUND
# ========================================
@router.delete(
    "/{refund_id}"
)
def delete_refund(

    refund_id: int,

    db: Session = Depends(get_db)

):

    service = RefundService(db)


    return service.delete_refund(
        refund_id
    )