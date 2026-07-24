from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import async_get_db
from app.models.auth import User
from app.models.quotations import Quotation,QuotationItem
from app.schemas.quotations import (
    QuotationCreate,
    QuotationUpdate,
)
# from app.utils.role_based import get_current_user
from app.utils.vendor import calculate_item_totals, select_best_quotation
from app.models.vendor import Vendor
from app.utils.qr_code import generate_qr

from app.core.security import (
    async_get_db,
    get_current_user,
    require_roles
)

# router = APIRouter(prefix="/quotations", tags=["Quotations"])
router = APIRouter(
    prefix="/quotations",
    tags=["Quotations"],
    dependencies=[Depends(require_roles("superadmin"))]
)

def serialize_quotation(q: Quotation):
    return {
        "id": q.id,
        "vendor_id": q.vendor_id,
        "vendor_name": q.vendor_name,
        "invoice_no": q.invoice_no,
        "quotation_date": q.quotation_date,
        "total_amount": q.total_amount,
        "total_discount": q.total_discount,
        "net_amount": q.net_amount,
        "is_approved": q.is_approved,
        "items": [
            {
                "id": i.id,
                "medicine_name": i.medicine_name,
                "dosage": i.dosage,
                "quantity": i.quantity,
                "mrp": i.mrp,
                "price": i.price,
                "cgst": i.cgst,
                "sgst": i.sgst,
                "total_price": i.total_price,
                "discount_price": i.discount_price,
                "final_price": i.final_price,
            }
            for i in q.items
        ],
    }



#
# @router.post("/")
# async def create_quotation(
#     data: QuotationCreate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.current_branch_id
#
#     # Validate Vendor (Tenant Safe)
#     result = await db.execute(
#         select(Vendor).where(
#             Vendor.id == data.vendor_id,
#             Vendor.hospital_id == hospital_id,
#             Vendor.branch_id == branch_id
#         )
#     )
#     vendor = result.scalar_one_or_none()
#
#     if not vendor:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid vendor for this hospital/branch"
#         )
#
#     invoice_no = data.invoice_no or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
#
#     quotation = Quotation(
#         vendor_name=data.vendor_name,
#         drug_license_no=data.drug_license_no,
#         gst_no=data.gst_no,
#         place_of_supply=data.place_of_supply,
#         invoice_no=invoice_no,
#         quotation_date=data.quotation_date,
#         vendor_id=data.vendor_id,
#         total_amount=0.0,
#         total_discount=0.0,
#         net_amount=0.0,
#         is_approved=False,
#         hospital_id=hospital_id,
#         branch_id=branch_id
#     )
#
#     total_amount = 0.0
#     total_discount = 0.0
#
#     for item in data.items:
#         total_price, final_price = calculate_item_totals(
#             price=item.price,
#             quantity=item.quantity,
#             cgst=item.cgst,
#             sgst=item.sgst,
#             discount=item.discount_price
#         )
#
#         quotation_item = QuotationItem(
#             medicine_name=item.medicine_name,
#             dosage=item.dosage,
#             quantity=item.quantity,
#             mrp=item.mrp,
#             price=item.price,
#             cgst=item.cgst,
#             sgst=item.sgst,
#             total_price=total_price,
#             discount_price=item.discount_price,
#             final_price=final_price,
#             hospital_id=hospital_id,
#             branch_id=branch_id
#         )
#
#         quotation.items.append(quotation_item)
#
#         total_amount += total_price
#         total_discount += item.discount_price
#
#     quotation.total_amount = total_amount
#     quotation.total_discount = total_discount
#     quotation.net_amount = total_amount - total_discount
#
#     db.add(quotation)
#     await db.commit()
#     await db.refresh(quotation)
#
#     return quotation
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

@router.post("/")
async def create_quotation(
    data: QuotationCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        hospital_id = current_user.hospital_id
        branch_id = current_user.current_branch_id

        # Validate Vendor
        result = await db.execute(
            select(Vendor).where(
                Vendor.id == data.vendor_id,
                Vendor.hospital_id == hospital_id,
                Vendor.branch_id == branch_id
            )
        )
        vendor = result.scalar_one_or_none()

        if not vendor:
            raise HTTPException(
                status_code=400,
                detail="Invalid vendor for this hospital/branch"
            )

        invoice_no = data.invoice_no or f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        quotation = Quotation(
            vendor_name=data.vendor_name,
            drug_license_no=data.drug_license_no,
            gst_no=data.gst_no,
            place_of_supply=data.place_of_supply,
            invoice_no=invoice_no,
            quotation_date=data.quotation_date,
            vendor_id=data.vendor_id,
            total_amount=0.0,
            total_discount=0.0,
            net_amount=0.0,
            is_approved=False,
            hospital_id=hospital_id,
            branch_id=branch_id
        )

        total_amount = 0.0
        total_discount = 0.0

        for item in data.items:
            total_price, final_price = calculate_item_totals(
                price=item.price,
                quantity=item.quantity,
                cgst=item.cgst,
                sgst=item.sgst,
                discount=item.discount_price
            )

            quotation_item = QuotationItem(
                medicine_name=item.medicine_name,
                dosage=item.dosage,
                quantity=item.quantity,
                mrp=item.mrp,
                price=item.price,
                cgst=item.cgst,
                sgst=item.sgst,
                total_price=total_price,
                discount_price=item.discount_price,
                final_price=final_price,
                hospital_id=hospital_id,
                branch_id=branch_id
            )

            quotation.items.append(quotation_item)

            total_amount += total_price
            total_discount += item.discount_price

        quotation.total_amount = total_amount
        quotation.total_discount = total_discount
        quotation.net_amount = total_amount - total_discount

        db.add(quotation)
        await db.commit()
        await db.refresh(quotation)

        return quotation

    except IntegrityError as e:
        await db.rollback()

        error = str(e.orig)

        if "cannot be null" in error.lower():
            field = error.split("'")[1]
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required."
            )

        raise HTTPException(
            status_code=400,
            detail=error
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# @router.get("/best/{medicine_name}")
# async def get_best_quotation(
#     medicine_name: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(Quotation)
#         .join(Quotation.items)
#         .where(QuotationItem.medicine_name == medicine_name)
#     )
#
#     quotations = result.scalars().unique().all()
#
#     if not quotations:
#         raise HTTPException(status_code=404, detail="No quotations found")
#
#     best = select_best_quotation(quotations)
#
#     best.is_approved = True
#     await db.commit()
#     # await db.refresh(best)
#     await db.refresh(quotations, attribute_names=["items"])
#
#     return best

# @router.get("/best/{medicine_name}")
# async def get_best_quotation(
#     medicine_name: str,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(Quotation)
#         .join(Quotation.items)
#         .where(
#             QuotationItem.medicine_name == medicine_name,
#             Quotation.hospital_id == hospital_id,
#             Quotation.branch_id == branch_id
#         )
#     )
#
#     quotations = result.scalars().unique().all()
#
#     if not quotations:
#         raise HTTPException(status_code=404, detail="No quotations found")
#
#     best = select_best_quotation(quotations)
#
#     best.is_approved = True
#     await db.commit()
#     await db.refresh(best)
#
#     return best

from sqlalchemy.orm import selectinload

@router.get("/best/{medicine_name}")
async def get_best_quotation(
    medicine_name: str,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(Quotation)
        .options(
            selectinload(Quotation.vendor),
            selectinload(Quotation.items)
        )
        .join(Quotation.items)
        .where(
            QuotationItem.medicine_name == medicine_name,
            Quotation.hospital_id == hospital_id,
            Quotation.branch_id == branch_id
        )
    )

    quotations = result.scalars().unique().all()

    if not quotations:
        raise HTTPException(
            status_code=404,
            detail="No quotations found"
        )

    best = select_best_quotation(quotations)

    best.is_approved = True

    await db.commit()
    await db.refresh(best)

    return best

# @router.put("/{quotation_id}")
# async def update_quotation(
#     quotation_id: int,
#     data: QuotationUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(Quotation).where(Quotation.id == quotation_id)
#     )
#     quotation = result.scalar_one_or_none()
#
#     if not quotation:
#         raise HTTPException(status_code=404, detail="Quotation not found")
#
#     for field, value in data.dict(exclude_unset=True).items():
#         setattr(quotation, field, value)
#
#     await db.commit()
#     await db.refresh(quotation)
#
#     return quotation

# @router.put("/{quotation_id}")
# async def update_quotation(
#     quotation_id: int,
#     data: QuotationUpdate,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.current_branch_id
#
#     result = await db.execute(
#         select(Quotation).where(
#             Quotation.id == quotation_id,
#             Quotation.hospital_id == hospital_id,
#             Quotation.branch_id == branch_id
#         )
#     )
#     quotation = result.scalar_one_or_none()
#
#     if not quotation:
#         raise HTTPException(status_code=404, detail="Quotation not found")
#
#     for field, value in data.dict(exclude_unset=True).items():
#         setattr(quotation, field, value)
#
#     await db.commit()
#     await db.refresh(quotation)
#
#     return quotation

@router.put("/{quotation_id}")
async def update_quotation(
    quotation_id: int,
    data: QuotationUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        hospital_id = current_user.hospital_id
        branch_id = current_user.current_branch_id

        result = await db.execute(
            select(Quotation).where(
                Quotation.id == quotation_id,
                Quotation.hospital_id == hospital_id,
                Quotation.branch_id == branch_id
            )
        )
        quotation = result.scalar_one_or_none()

        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found")

        if not data.vendor_name:
            raise HTTPException(status_code=400, detail="vendor_name is required")

        if not data.gst_no:
            raise HTTPException(status_code=400, detail="gst_no is required")

        if not data.quotation_date:
            raise HTTPException(status_code=400, detail="quotation_date is required")

        if not data.invoice_no:
            raise HTTPException(status_code=400, detail="invoice_no is required")

        for field, value in data.dict(exclude_unset=True).items():
            setattr(quotation, field, value)

        await db.commit()
        await db.refresh(quotation)

        return quotation

    except IntegrityError as e:
        await db.rollback()

        error = str(e.orig)

        if "cannot be null" in error.lower():
            field = error.split("'")[1]
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required."
            )

        raise HTTPException(
            status_code=400,
            detail=error
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# @router.get("/search")
# async def search_quotations_by_vendor(
#     vendor_name: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(Quotation)
#         .where(Quotation.vendor_name.ilike(f"%{vendor_name}%"))
#     )
#
#     quotations = result.scalars().all()
#
#     if not quotations:
#         raise HTTPException(
#             status_code=404,
#             detail="No quotations found for this vendor"
#         )
#
#     return quotations
@router.get("/search")
async def search_quotations_by_vendor(
    vendor_name: str,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(Quotation).where(
            Quotation.vendor_name.ilike(f"%{vendor_name}%"),
            Quotation.hospital_id == hospital_id,
            Quotation.branch_id == branch_id
        )
    )

    quotations = result.scalars().all()

    if not quotations:
        raise HTTPException(
            status_code=404,
            detail="No quotations found for this vendor"
        )

    return quotations

# @router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_quotation(
#     quotation_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(Quotation).where(Quotation.id == quotation_id)
#     )
#     quotation = result.scalar_one_or_none()
#
#     if not quotation:
#         raise HTTPException(status_code=404, detail="Quotation not found")
#
#     await db.delete(quotation)
#     await db.commit()


# @router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_quotation(
#     quotation_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(Quotation).where(
#             Quotation.id == quotation_id,
#             Quotation.hospital_id == hospital_id,
#             Quotation.branch_id == branch_id
#         )
#     )
#     quotation = result.scalar_one_or_none()
#
#     if not quotation:
#         raise HTTPException(status_code=404, detail="Quotation not found")
#
#     await db.delete(quotation)
#     await db.commit()

@router.delete("/{quotation_id}")
async def delete_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(async_get_db),
        current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(Quotation).where(
            Quotation.id == quotation_id,
            Quotation.hospital_id == hospital_id,
            Quotation.branch_id == branch_id
        )
    )

    quotation = result.scalar_one_or_none()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    await db.delete(quotation)
    await db.commit()

    return {
        "success": True,
        "message": "Quotation deleted successfully"
    }

@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)