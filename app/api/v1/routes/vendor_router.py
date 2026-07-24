from datetime import datetime
from aiosmtplib import status
from fastapi import APIRouter, Depends, HTTPException, Query,Body
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.auth import User
from app.services.vendor import calculate_vendor_payable
from app.db.base import Base
from app.core.security import async_get_db, get_current_user
from app.models.entry_models import StockLedger, Batch
from app.models.vendor import Vendor
from app.schemas.vendor import VALID_STATUSES, VendorOut, VendorCreate, VendorStatusUpdate, VendorUpdate, \
    VendorReturnOut, VendorReturnCreate
from app.core.security import require_roles
from app.utils.vendor import get_vendor_by_id, get_vendor_by_gst, calculate_rating
from app.utils.qr_code import generate_qr
from app.models.vendor import VendorTransaction
from app.schemas.vendor import VendorOut
from app.schemas.vendor import VendorTransactionCreate

router = APIRouter(
    prefix="/vendor",
    tags=["Vendor"],
    dependencies=[Depends(require_roles("superadmin"))]
)


@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)


# ------------------ CREATE VENDOR ------------------

# @router.post("/", response_model=VendorOut)
# async def create_vendor(
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     data: VendorCreate = ...,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.current_branch_id
#
#     # Check GST uniqueness within same hospital + branch
#     if data.gst_no:
#         existing = await db.execute(
#             select(Vendor).where(
#                 and_(
#                     Vendor.gst_no == data.gst_no,
#                     Vendor.hospital_id == hospital_id,
#                     Vendor.branch_id == branch_id
#                 )
#             )
#         )
#         if existing.scalar_one_or_none():
#             raise HTTPException(
#                 status_code=400,
#                 detail="Vendor with this GST already exists in this hospital/branch"
#             )
#
#     vendor = Vendor(
#         **data.dict(),
#         hospital_id=hospital_id,
#         branch_id=branch_id
#     )
#     vendor.rating = calculate_rating(vendor)
#
#     db.add(vendor)
#     await db.commit()
#     await db.refresh(vendor)
#     return vendor
#

@router.post("/", response_model=VendorOut)
async def create_vendor(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    data: VendorCreate = ...,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    try:
        # Check GST uniqueness
        if data.gst_no:
            existing = await db.execute(
                select(Vendor).where(
                    and_(
                        Vendor.gst_no == data.gst_no,
                        Vendor.hospital_id == hospital_id,
                        Vendor.branch_id == branch_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail="Vendor with this GST already exists in this hospital/branch"
                )

        vendor = Vendor(
            **data.dict(),
            hospital_id=hospital_id,
            branch_id=branch_id
        )

        vendor.rating = calculate_rating(vendor)

        db.add(vendor)
        await db.commit()
        await db.refresh(vendor)

        return vendor

    except TypeError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field provided: {str(e)}"
        )

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Database integrity error. Please check required fields or duplicate values."
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ------------------ LIST VENDORS ------------------

@router.get("/", response_model=list[VendorOut])
async def list_vendors(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Vendor).where(
            and_(
                Vendor.hospital_id == hospital_id,
                Vendor.branch_id == branch_id,
                Vendor.is_active == True
            )
        )
    )
    return result.scalars().all()


# ------------------ SEARCH VENDORS ------------------

@router.get("/search", response_model=list[VendorOut])
async def search_vendors(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    name: str | None = Query(None),
    pincode: str | None = Query(None),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Vendor).where(
        and_(
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id,
            Vendor.is_active == True
        )
    )

    if name:
        query = query.where(Vendor.name.ilike(f"%{name}%"))

    if pincode:
        query = query.where(Vendor.pincode.ilike(f"%{pincode}%"))

    result = await db.execute(query)
    return result.scalars().all()


# ------------------ GET SINGLE VENDOR ------------------

@router.get("/{vendor_id}", response_model=VendorOut)
async def get_vendor(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Vendor).where(
            and_(
                Vendor.id == vendor_id,
                Vendor.hospital_id == hospital_id,
                Vendor.branch_id == branch_id,
                Vendor.is_active == True
            )
        )
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    return vendor


# ------------------ UPDATE VENDOR ------------------

# @router.put("/{vendor_id}", response_model=VendorOut)
# async def update_vendor(
#     vendor_id: int,
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     data: VendorUpdate = ...,
#     db: AsyncSession = Depends(async_get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     result = await db.execute(
#         select(Vendor).where(
#             and_(
#                 Vendor.id == vendor_id,
#                 Vendor.hospital_id == hospital_id,
#                 Vendor.branch_id == branch_id,
#                 Vendor.is_active == True
#             )
#         )
#     )
#     vendor = result.scalar_one_or_none()
#
#     if not vendor:
#         raise HTTPException(status_code=404, detail="Vendor not found")
#
#     for key, value in data.dict(exclude_unset=True).items():
#         setattr(vendor, key, value)
#
#     vendor.rating = calculate_rating(vendor)
#
#     await db.commit()
#     await db.refresh(vendor)
#     return vendor

@router.put("/{vendor_id}", response_model=VendorOut)
async def update_vendor(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    data: VendorUpdate = ...,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await db.execute(
            select(Vendor).where(
                and_(
                    Vendor.id == vendor_id,
                    Vendor.hospital_id == hospital_id,
                    Vendor.branch_id == branch_id,
                    Vendor.is_active == True
                )
            )
        )
        vendor = result.scalar_one_or_none()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        if not data.email:
            raise HTTPException(status_code=404, detail="email is required")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(vendor, key, value)

        vendor.rating = calculate_rating(vendor)

        await db.commit()
        await db.refresh(vendor)

        return vendor

    except IntegrityError as e:
        await db.rollback()

        error = str(e.orig)

        if "cannot be null" in error.lower():
            field = error.split("'")[1]
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required."
            )

        elif "foreign key constraint fails" in error.lower():
            raise HTTPException(
                status_code=400,
                detail="Invalid hospital_id or branch_id."
            )

        raise HTTPException(
            status_code=400,
            detail=error
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# ------------------ SOFT DELETE ------------------

@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Vendor).where(
            and_(
                Vendor.id == vendor_id,
                Vendor.hospital_id == hospital_id,
                Vendor.branch_id == branch_id,
                Vendor.is_active == True
            )
        )
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_active = False
    await db.commit()
    return {"message": "Vendor deactivated successfully"}


# ------------------ QR ------------------

# @router.get("/qr")
# async def medicine_docs_qr():
#     url = "http://localhost:8000/docs#/Medicines"
#     return generate_qr(url)


async def validate_vendor_for_po(vendor_id: int, db: AsyncSession):
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if vendor.rating == "Blacklisted":
        raise HTTPException(
            status_code=400,
            detail="Blacklisted vendors cannot receive purchase orders"
        )

    return vendor


# ------------------ ADD VENDOR TRANSACTION ------------------

# @router.post("/{vendor_id}/transaction", response_model=dict)
# async def add_vendor_transaction(
#     vendor_id: int,
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     data: VendorTransactionCreate = ...,
#     db: AsyncSession = Depends(get_db)
# ):
#     # Validate vendor
#     vendor = await get_vendor_by_id(db, vendor_id, hospital_id, branch_id)
#     if not vendor:
#         raise HTTPException(status_code=404, detail="Vendor not found")

#     if data.type not in ["credit", "debit"]:
#         raise HTTPException(status_code=400, detail="Invalid type")

#     transaction = VendorTransaction(
#         vendor_id=vendor_id,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         type=data.type,
#         amount=data.amount,
#         reference=data.reference,
#         notes=data.notes
#     )

#     db.add(transaction)
#     await db.commit()

#     payable = await calculate_vendor_payable(db, vendor_id, hospital_id, branch_id)

#     return {
#         "message": "Transaction added",
#         "current_payable": payable
#     }

@router.post("/{vendor_id}/transaction", response_model=dict)
async def add_vendor_transaction(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    data: VendorTransactionCreate = Body(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    # Check Vendor Exists
    vendor = await get_vendor_by_id(
        db,
        vendor_id,
        hospital_id,
        branch_id
    )

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    # Validate Type
    if data.type not in ["credit", "debit"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid type"
        )

    # Save Transaction
    transaction = VendorTransaction(
        vendor_id=vendor_id,
        hospital_id=hospital_id,
        branch_id=branch_id,
        type=data.type,
        amount=data.amount,
        reference=data.reference,
        notes=data.notes
    )

    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)

    # Calculate Current Payable
    payable = await calculate_vendor_payable(
        db,
        vendor_id,
        hospital_id,
        branch_id
    )

    return {
        "message": "Transaction added successfully",
        "transaction_id": transaction.id,
        "current_payable": payable
    }

# ------------------ GET VENDOR PAYABLE ------------------

@router.get("/{vendor_id}/payable")
async def get_vendor_payable(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = await get_vendor_by_id(db, vendor_id, hospital_id, branch_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    payable = await calculate_vendor_payable(db, vendor_id, hospital_id, branch_id)

    return {
        "vendor_id": vendor_id,
        "payable": payable
    }

# ------------------ VENDOR TRANSACTION HISTORY ------------------

@router.get("/{vendor_id}/transactions")
async def get_vendor_transactions(
    vendor_id: int,
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(VendorTransaction).where(
            VendorTransaction.vendor_id == vendor_id,
            VendorTransaction.hospital_id == hospital_id,
            VendorTransaction.branch_id == branch_id
        ).order_by(VendorTransaction.created_at.desc())
    )

    return result.scalars().all()





@router.patch("/{vendor_id}/status", response_model=VendorOut)
async def update_vendor_status(
    vendor_id: int,
    data: VendorStatusUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be: {VALID_STATUSES}")

    vendor = await db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    if vendor.status == data.status:
        raise HTTPException(400, f"Vendor is already {data.status}")

    vendor.status = data.status
    await db.commit()
    await db.refresh(vendor)
    return VendorOut.model_validate(vendor)










#
#
#
# @router.post(
#     "/",
#     response_model=VendorReturnOut,
# )
# async def create_vendor_return(
#     data: VendorReturnCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(
#         role_required([
#             "ADMIN",
#             "PHARMACIST",
#             "SUPERADMIN"
#         ])
#     )
# ):
#
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     # -----------------------------------------------------
#     # VENDOR CHECK
#     # -----------------------------------------------------
#
#     vendor_result = await db.execute(
#         select(Vendor).where(
#             Vendor.id == data.vendor_id
#         )
#     )
#
#     vendor = vendor_result.scalar_one_or_none()
#
#     if not vendor:
#         raise HTTPException(
#             status_code=404,
#             detail="Vendor not found"
#         )
#
#     # -----------------------------------------------------
#     # CREATE RETURN HEADER
#     # -----------------------------------------------------
#
#     return_number = (
#         f"RTV-{int(datetime.utcnow().timestamp())}"
#     )
#
#     vendor_return = VendorReturn(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         vendor_id=data.vendor_id,
#         grn_id=data.grn_id,
#         return_number=return_number,
#         reason=data.reason,
#         status="PENDING",
#         created_at=datetime.utcnow()
#     )
#
#     db.add(vendor_return)
#
#     await db.flush()
#
#     # -----------------------------------------------------
#     # PROCESS ITEMS
#     # -----------------------------------------------------
#
#     for item in data.items:
#
#         batch = await db.get(Batch, item.batch_id)
#
#         if not batch:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f"Batch {item.batch_id} not found"
#             )
#
#         # stock check
#         if batch.quantity_available < item.quantity:
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     f"Insufficient stock "
#                     f"for batch {batch.batch_number}"
#                 )
#             )
#
#         # reduce stock
#         batch.quantity_available -= item.quantity
#
#         # create return item
#         return_item = VendorReturnItem(
#             vendor_return_id=vendor_return.id,
#             batch_id=item.batch_id,
#             medicine_id=batch.medicine_id,
#             quantity=item.quantity,
#             reason=item.reason
#         )
#
#         db.add(return_item)
#
#         # stock ledger entry
#         ledger = StockLedger(
#             batch_id=batch.id,
#             batch_type="medicine",
#             hospital_id=hospital_id,
#             branch_id=branch_id,
#             transaction_type="RETURN_TO_VENDOR",
#             quantity_in=0,
#             quantity_out=item.quantity,
#             balance_qty=batch.quantity_available,
#             transaction_value=(
#                 item.quantity * (batch.cost_price or 0)
#             ),
#             remarks=(
#                 f"Vendor return "
#                 f"{return_number}"
#             )
#         )
#
#         db.add(ledger)
#
#     await db.commit()
#
#     # reload with items
#     result = await db.execute(
#         select(VendorReturn)
#         .options(
#             selectinload(VendorReturn.items)
#         )
#         .where(
#             VendorReturn.id == vendor_return.id
#         )
#     )
#
#     vendor_return = result.scalar_one()
#
#     return vendor_return
#
#
# # =========================================================
# # LIST RETURNS
# # =========================================================
#
# @router.get(
#     "/",
#     response_model=list[VendorReturnOut]
# )
# async def list_vendor_returns(
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(
#         role_required([
#             "ADMIN",
#             "PHARMACIST",
#             "SUPERADMIN"
#         ])
#     )
# ):
#
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(VendorReturn)
#         .options(
#             selectinload(VendorReturn.items)
#         )
#         .where(
#             VendorReturn.hospital_id == hospital_id,
#             VendorReturn.branch_id == branch_id
#         )
#         .order_by(VendorReturn.id.desc())
#     )
#
#     return result.scalars().unique().all()
#
#
# # =========================================================
# # GET SINGLE RETURN
# # =========================================================
#
# @router.get(
#     "/{return_id}",
#     response_model=VendorReturnOut
# )
# async def get_vendor_return(
#     return_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(
#         role_required([
#             "ADMIN",
#             "PHARMACIST",
#             "SUPERADMIN"
#         ])
#     )
# ):
#
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(VendorReturn)
#         .options(
#             selectinload(VendorReturn.items)
#         )
#         .where(
#             VendorReturn.id == return_id,
#             VendorReturn.hospital_id == hospital_id,
#             VendorReturn.branch_id == branch_id
#         )
#     )
#
#     vendor_return = result.scalar_one_or_none()
#
#     if not vendor_return:
#         raise HTTPException(
#             status_code=404,
#             detail="Vendor return not found"
#         )
#
#     return vendor_return
#
#
# # =========================================================
# # UPDATE STATUS
# # =========================================================
#
# @router.put("/{return_id}/status")
# async def update_return_status(
#     return_id: int,
#     status_value: str,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(
#         role_required([
#             "ADMIN",
#             "PHARMACIST",
#             "SUPERADMIN"
#         ])
#     )
# ):
#
#     vendor_return = await db.get(
#         VendorReturn,
#         return_id
#     )
#
#     if not vendor_return:
#         raise HTTPException(
#             status_code=404,
#             detail="Vendor return not found"
#         )
#
#     allowed_status = [
#         "PENDING",
#         "APPROVED",
#         "PICKED_UP",
#         "CREDIT_RECEIVED",
#         "REJECTED"
#     ]
#
#     if status_value not in allowed_status:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid status"
#         )
#
#     vendor_return.status = status_value
#
#     await db.commit()
#
#     return {
#         "message": (
#             f"Status updated to "
#             f"{status_value}"
#         )
#     }