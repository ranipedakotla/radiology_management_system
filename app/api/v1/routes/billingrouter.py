# from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from app.core.security import async_get_db
from app.models.role_based import BillingSummary
from app.schemas.role_based import BillingSummaryCreate, BillingSummaryResponse, BillingSummaryUpdate
from app.core.security import require_roles
from datetime import date
from app.utils.qr_code import generate_qr
from app.models.appointments import Appointment

router = APIRouter(prefix="/billingrouter", tags=["Billingrouter"])


# @router.post("/", response_model=BillingSummaryResponse)
# async def create_billing_summary(
#     data: BillingSummaryCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["accounting","pharmacist"]))
# ):
#     total = data.cash_amount + data.upi_amount + data.card_amount
#
#     billing = BillingSummary(
#         **data.dict(),
#         total_amount=total
#     )
#
#     db.add(billing)
#     await db.commit()
#     await db.refresh(billing)
#     return billing

# @router.post("/", response_model=BillingSummaryResponse)
# async def create_billing_summary(
#     data: BillingSummaryCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["accounting", "pharmacist"]))
# ):
#     total = data.cash_amount + data.upi_amount + data.card_amount
#
#     billing_data = data.dict()
#     billing_data.pop("total_amount", None)
#
#     billing = BillingSummary(
#         **billing_data,
#         hospital_id=current_user.hospital_id,
#         branch_id=current_user.branch_id,
#         # total_amount=total
#     )
#
#     db.add(billing)
#
#     await db.commit()
#     await db.refresh(billing)
#
#     return billing

@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)


@router.post("/", response_model=BillingSummaryResponse)
async def create_billing_summary(
    data: BillingSummaryCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["accounting", "pharmacist","superadmin"]))
):
    # safety check
    if not current_user.hospital_id or not current_user.current_branch_id:
        raise HTTPException(status_code=400, detail="Invalid user context")

    total = data.cash_amount + data.upi_amount + data.card_amount


    appointment_result = await db.execute(
        select(Appointment).where(
            Appointment.id == data.appointment_id,
            Appointment.hospital_id == current_user.hospital_id,
            Appointment.branch_id == current_user.current_branch_id
        )
    )

    appointment = appointment_result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    billing = BillingSummary(
        **data.dict(),
        hospital_id=current_user.hospital_id,
        branch_id=current_user.current_branch_id,
        total_amount=total
    )

    db.add(billing)

    try:
        await db.commit()
        await db.refresh(billing)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return billing


@router.get("/by-date", response_model=list[BillingSummaryResponse])
async def get_billing_by_date(
    billing_date: date,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["accounting", "pharmacist","superadmin"]))):
    result = await db.execute(
        select(BillingSummary).where(
            BillingSummary.bill_date == billing_date
        )
    )
    return result.scalars().all()



@router.get("/{billing_id}", response_model=BillingSummaryResponse)
async def get_billing_by_id(
    billing_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["accounting", "admin","pharmacist"]))
):
    result = await db.execute(
        select(BillingSummary).where(BillingSummary.id == billing_id)
    )
    billing = result.scalar_one_or_none()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    return billing
#
# @router.get(
#     "/appointment/{appointment_id}",
#     response_model=BillingSummaryResponse
# )
# async def get_billing_by_appointment(
#     appointment_id: int,
#     db: AsyncSession = Depends(async_get_db)
# ):
#     result = await db.execute(
#         select(BillingSummary).where(
#             BillingSummary.appointment_id == appointment_id
#         )
#     )
#
#     billing = result.scalar_one_or_none()
#
#     if not billing:
#         raise HTTPException(
#             status_code=404,
#             detail="Billing record not found"
#         )
#
#     return billing


# @router.get("/by-date", response_model=list[BillingSummaryResponse])
# async def get_billing_by_date(
#     billing_date: date,
#     db: AsyncSession = Depends(get_db),
# ):
#     result = await db.execute(
#         select(BillingSummary).where(
#             BillingSummary.billing_date == billing_date
#         )
#     )
#     return result.scalars().all()

# @router.put("/{billing_id}", response_model=BillingSummaryResponse)
# async def update_billing(
#     billing_id: int,
#     date: str,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["accounting","pharmacist"]))
# ):
#     result = await db.execute(
#         select(BillingSummary).where(BillingSummary.id == billing_id)
#     )
#     billing = result.scalar_one_or_none()
#
#     if not billing:
#         raise HTTPException(status_code=404, detail="Billing record not found")
#
#     for field, value in date.dict(exclude_unset=True).items():
#         setattr(billing, field, value)
#
#     #  Recalculate total
#     billing.total_amount = (
#         billing.cash_amount +
#         billing.upi_amount +
#         billing.card_amount
#     )
#
#     await db.commit()
#     await db.refresh(billing)
#     return billing

@router.put("/{billing_id}", response_model=BillingSummaryResponse)
async def update_billing(
    billing_id: int,
    payload: BillingSummaryUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["accounting","pharmacist","superadmin"]))
):
    result = await db.execute(
        select(BillingSummary).where(BillingSummary.id == billing_id)
    )
    billing = result.scalar_one_or_none()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    # update only provided fields
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(billing, field, value)

    # recompute total
    billing.total_amount = (
        billing.cash_amount +
        billing.upi_amount +
        billing.card_amount
    )

    await db.commit()
    await db.refresh(billing)
    return billing

@router.delete("/{billing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing(
    billing_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["admin","pharmacist","superadmin"]))
):
    result = await db.execute(
        select(BillingSummary).where(BillingSummary.id == billing_id)
    )
    billing = result.scalar_one_or_none()

    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")

    await db.delete(billing)
    await db.commit()

    # return {
    #     "message": "Billing deleted successfully"
    # }



