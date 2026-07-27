from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.security import get_db

from app.schemas.radiology_refund import (
    RefundResponse,
)

from app.services.radiology_refund import (
    RadiologyRefundService,
)


router = APIRouter(
    prefix="/radiology-refunds",
    tags=["Radiology Refund"]
)


# ========================================
# CREATE REFUND
# ========================================
@router.post(
    "/",
    response_model=RefundResponse,
    status_code=201
)
def create_radiology_refund(

    registration_id: int = Form(
        ...
    ),

    refund_amount: float = Form(
        ...
    ),

    refund_reason: str = Form(
        ...
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyRefundService(
        db
    )

    return service.create_refund(

        registration_id=registration_id,

        refund_amount=refund_amount,

        refund_reason=refund_reason,

        remarks=remarks,
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
def get_all_radiology_refunds(

    db: Session = Depends(get_db)
):

    service = RadiologyRefundService(
        db
    )

    return service.get_all_refunds()


# ========================================
# GET REFUND BY ID
# ========================================
@router.get(
    "/{refund_id}",
    response_model=RefundResponse
)
def get_radiology_refund(

    refund_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyRefundService(
        db
    )

    return service.get_refund(
        refund_id
    )


# ========================================
# UPDATE REFUND
# ========================================
@router.put(
    "/{refund_id}",
    response_model=RefundResponse
)
def update_radiology_refund(

    refund_id: int,

    refund_amount: float | None = Form(
        default=None
    ),

    refund_reason: str | None = Form(
        default=None
    ),

    status_value: str | None = Form(
        default=None
    ),

    remarks: str | None = Form(
        default=None
    ),

    db: Session = Depends(get_db)
):

    service = RadiologyRefundService(
        db
    )

    return service.update_refund(

        refund_id=refund_id,

        refund_amount=refund_amount,

        refund_reason=refund_reason,

        status_value=status_value,

        remarks=remarks,
    )


# ========================================
# DELETE REFUND
# ========================================
@router.delete(
    "/{refund_id}"
)
def delete_radiology_refund(

    refund_id: int,

    db: Session = Depends(get_db)
):

    service = RadiologyRefundService(
        db
    )

    return service.delete_refund(
        refund_id
    )