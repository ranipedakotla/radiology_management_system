from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import async_get_db
from app.models.discounts import DiscountAudit
from app.schemas.discount import (
    DiscountAuditCreate,
    DiscountAuditResponse,
)
from app.models.auth import (User)
from app.core.security import get_current_user, detect_discount_abuse, require_roles
from app.utils.qr_code import generate_qr

router = APIRouter(prefix="/discounts", tags=["Discount Audit"])


# @router.post("/", response_model=DiscountAuditResponse)
# async def log_discount(
#     data: DiscountAuditCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "pharmacist":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     discount = DiscountAudit(
#         pharmacist_id=current_user.id,
#         applied_by=current_user.id,
#         bill_no=data.bill_id,
#         hospital_id=data.hospital_id,
#         branch_id=data.branch_id,
#         customer_id=data.customer_id,
#         discount_type=data.discount_type,
#         discount_value=data.discount_value,
#         discount_date=data.discount_date,
#         reference_info=data.reference_info
#     )
#
#     db.add(discount)
#     await db.commit()
#     await db.refresh(discount)
#
#     return discount

@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)


@router.post("/", response_model=DiscountAuditResponse)
async def log_discount(
    data: DiscountAuditCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["pharmacist","superadmin"]))
):
    discount = DiscountAudit(
        pharmacist_id=current_user.id,
        applied_by=current_user.id,
        bill_no=data.bill_id,
        hospital_id=data.hospital_id,
        branch_id=data.branch_id,
        customer_id=data.customer_id,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        discount_date=data.discount_date,
        reference_info=data.reference_info
    )

    db.add(discount)
    await db.commit()
    await db.refresh(discount)

    return discount

# @router.get("/audit/{pharmacist_id}")
# async def audit_discounts(
#     pharmacist_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "accounting":
#         raise HTTPException(status_code=403, detail="Access denied")
#
#     result = await db.execute(
#         select(DiscountAudit).where(
#             DiscountAudit.pharmacist_id == pharmacist_id
#         )
#     )
#
#     discounts = result.scalars().all()
#
#     abuse, reason = detect_discount_abuse(discounts)
#
#     return {
#         "discounts": discounts,
#         "abuse_detected": abuse,
#         "reason": reason
#     }


@router.get("/audit/{pharmacist_id}")
async def audit_discounts(
    pharmacist_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["pharmacist","superadmin"]))
):
    abuse, reason = await detect_discount_abuse(pharmacist_id, db)

    result = await db.execute(
        select(DiscountAudit).where(
            DiscountAudit.pharmacist_id == pharmacist_id
        )
    )

    discounts = result.scalars().all()

    return {
        "discounts": discounts,
        "abuse_detected": abuse,
        "reason": reason
    }

@router.get("/", response_model=list[DiscountAuditResponse])
async def get_all_discounts(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["admin","pharmacist","superadmin"]))
):
    # if current_user.role not in ["admin", "accounting"]:
    #     raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(select(DiscountAudit))
    return result.scalars().all()

@router.get("/{discount_id}", response_model=DiscountAuditResponse)
async def get_discount_by_id(
    discount_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(DiscountAudit).where(DiscountAudit.id == discount_id)
    )

    discount = result.scalar_one_or_none()

    if not discount:
        raise HTTPException(status_code=404, detail="Not found")

    if current_user.role == "pharmacist" and \
       discount.pharmacist_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return discount

@router.get("/my/logs", response_model=list[DiscountAuditResponse])
async def my_discount_logs(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["admin","pharmacist"]))
):
    # if current_user.role != "pharmacist":
    #     raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(DiscountAudit).where(
            DiscountAudit.pharmacist_id == current_user.id
        )
    )

    return result.scalars().all()

# @router.put("/{discount_id}", response_model=DiscountAuditResponse)
# async def update_discount(
#     discount_id: int,
#     data: DiscountAuditCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "admin":
#         raise HTTPException(status_code=403)
#
#     result = await db.execute(
#         select(DiscountAudit).where(DiscountAudit.id == discount_id)
#     )
#
#     discount = result.scalar_one_or_none()
#
#     if not discount:
#         raise HTTPException(status_code=404)
#
#     for field, value in data.dict().items():
#         setattr(discount, field, value)
#
#     await db.commit()
#     await db.refresh(discount)
#
#     return discount

@router.put("/{discount_id}", response_model=DiscountAuditResponse)
async def update_discount(
    discount_id: int,
    data: DiscountAuditCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["admin","pharmacist","superadmin"]))
):
    result = await db.execute(
        select(DiscountAudit).where(DiscountAudit.id == discount_id)
    )

    discount = result.scalar_one_or_none()

    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")

    for field, value in data.dict().items():
        setattr(discount, field, value)

    await db.commit()
    await db.refresh(discount)

    return discount

@router.delete("/{discount_id}")
async def delete_discount(
    discount_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_roles(["admin","pharmacist","superadmin"]))
):
    # if current_user.role != "admin":
    #     raise HTTPException(status_code=403)

    result = await db.execute(
        select(DiscountAudit).where(DiscountAudit.id == discount_id)
    )

    discount = result.scalar_one_or_none()

    if not discount:
        raise HTTPException(status_code=404)

    await db.delete(discount)
    await db.commit()

    return {"message": "Deleted successfully"}

