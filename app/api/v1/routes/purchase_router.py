from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_mail import  ConnectionConfig
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.auth import User
from app.schemas.vendor import VendorPaymentCreate
from app.utils.email import send_email
from app.utils.qr_code import generate_qr
from app.core.security import async_get_db
from app.models.vendor import Vendor
from app.models.entry_models import Medicine
from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import POCreate, POOut, POUpdate
from app.core.security import (
    async_get_db,
    get_current_user,
    require_roles
)

# from app.models.auth import User


# router = APIRouter(prefix="/po", tags=["Purchase Orders"])
# async def generate_po_number(db: AsyncSession) -> str:
#     result = await db.execute(select(func.max(PurchaseOrder.id)))
#     last_id = result.scalar() or 0
#     return f"PO-{last_id + 1:05d}"

# =========================
# EMAIL CONFIGURATION
# =========================

router = APIRouter(
    prefix="/po",
    tags=["Purchase Orders"],
    dependencies=[Depends(require_roles("superadmin"))]
)

conf = ConnectionConfig(
    MAIL_USERNAME="yourgmail@gmail.com",
    MAIL_PASSWORD="your_16_digit_app_password",
    MAIL_FROM="yourgmail@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def generate_po_number(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int
) -> str:
    result = await db.execute(
        select(func.max(PurchaseOrder.id)).where(
            PurchaseOrder.hospital_id == hospital_id,
                        PurchaseOrder.branch_id == branch_id
        )
    )
    last_id = result.scalar() or 0
    return f"PO-{hospital_id}-{branch_id}-{last_id + 1:05d}"

# @router.post("/", response_model=POOut, status_code=status.HTTP_201_CREATED)
# async def create_po(
#     data: POCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     # Validate Vendor
#     vendor = await db.get(Vendor, data.vendor_id)
#     if not vendor:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid vendor_id. Vendor does not exist."
#         )
#
#     # Validate Medicine
#     medicine = await db.get(Medicine, data.medicine_id)
#     if not medicine:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid medicine_id. Medicine does not exist."
#         )
#
#     po_number = await generate_po_number(db)
#
#     new_po = PurchaseOrder(
#         po_number=po_number,
#         vendor_id=data.vendor_id,
#         medicine_id=data.medicine_id,
#         quantity=data.quantity,
#         rate=data.rate,
#         discount=data.discount,
#         gst=data.gst,
#         delivery_location=data.delivery_location,
#         delivery_deadline=data.delivery_deadline,
#         terms=data.terms
#     )
#
#     db.add(new_po)
#     await db.commit()
#     await db.refresh(new_po)
#
#     return new_po

@router.get("/qr")
async def medicine_docs_qr():
    url = "http://localhost:8000/docs#/Medicines"
    return generate_qr(url)


#
@router.post("/", response_model=POOut, status_code=status.HTTP_201_CREATED)
async def create_po(
    data: POCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    # Logged in user tenant details
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    print("CURRENT USER:", current_user.id)
    print("HOSPITAL:", hospital_id)
    print("BRANCH:", branch_id)
    print("VENDOR ID:", data.vendor_id)
    print("MEDICINE ID:", data.medicine_id)

    # -------------------------------
    # Validate Vendor
    # -------------------------------
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
            detail=f"Invalid vendor_id {data.vendor_id} for hospital {hospital_id} branch {branch_id}"
        )
    if not data.delivery_location or not data.delivery_location.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery location is mandatory."
        )

    # -------------------------------
    # Validate Medicine
    # -------------------------------
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == data.medicine_id,
            Medicine.hospital_id == hospital_id,
            Medicine.branch_id == branch_id
        )
    )
    medicine = result.scalar_one_or_none()

    if not medicine:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid medicine_id {data.medicine_id} for hospital {hospital_id} branch {branch_id}"
        )

    # -------------------------------
    # Generate PO Number
    # -------------------------------
    po_number = await generate_po_number(
        db,
        hospital_id,
        branch_id
    )

    # -------------------------------
    # Create Purchase Order
    # -------------------------------
    new_po = PurchaseOrder(
        po_number=po_number,
        vendor_id=data.vendor_id,
        medicine_id=data.medicine_id,
        quantity=data.quantity,
        rate=data.rate,
        discount=data.discount,
        gst=data.gst,
        delivery_location=data.delivery_location,
        delivery_deadline=data.delivery_deadline,
        terms=data.terms,
        hospital_id=hospital_id,
        branch_id=branch_id
    )

    db.add(new_po)
    await db.commit()
    await db.refresh(new_po)

    return new_po
# @router.get("/", response_model=list[POOut])
# async def get_all_pos(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(PurchaseOrder))
#     return result.scalars().all()

@router.get("/", response_model=list[POOut])
async def get_all_pos(
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )
    return result.scalars().all()
#
# @router.get("/{po_id}", response_model=POOut)
# async def get_po_by_id(
#     po_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(PurchaseOrder).where(PurchaseOrder.id == po_id)
#     )
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=404, detail="Purchase Order not found")
#
#     return po
@router.get("/{po_id}", response_model=POOut)
async def get_po_by_id(
    po_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    return po

# @router.get("/number/{po_number}", response_model=POOut)
# async def get_po_by_number(
#     po_number: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
#     )
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=404, detail="Purchase Order not found")
#
#     return po
@router.get("/number/{po_number}", response_model=POOut)
async def get_po_by_number(
    po_number: str,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_number,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    return po

# @router.put("/{po_id}", response_model=POOut)
# async def update_po(
#     po_id: int,
#     data: POUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     result = await db.execute(
#         select(PurchaseOrder).where(PurchaseOrder.id == po_id)
#     )
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=404, detail="Purchase Order not found")
#
#     for field, value in data.dict(exclude_unset=True).items():
#         setattr(po, field, value)
#
#     await db.commit()
#     await db.refresh(po)
#     return po


@router.put("/{po_id}", response_model=POOut)
async def update_po(
    po_id: int,
    data: POUpdate,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        hospital_id = current_user.hospital_id
        branch_id = current_user.current_branch_id

        result = await db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.id == po_id,
                PurchaseOrder.hospital_id == hospital_id,
                PurchaseOrder.branch_id == branch_id
            )
        )
        po = result.scalar_one_or_none()

        if not po:
            raise HTTPException(status_code=404, detail="Purchase Order not found")

        # Validate medicine if it is being updated
        if data.medicine_id is not None:
            medicine_result = await db.execute(
                select(Medicine).where(
                    Medicine.id == data.medicine_id,
                    Medicine.hospital_id == hospital_id,
                    Medicine.branch_id == branch_id
                )
            )
            medicine = medicine_result.scalar_one_or_none()

            if not medicine:
                raise HTTPException(
                    status_code=400,
                    detail="Medicine not found."
                )

        update_data = data.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No data provided for update."
            )

        for field, value in update_data.items():
            setattr(po, field, value)

        await db.commit()
        await db.refresh(po)

        return po

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid data. Please verify the provided values."
        )

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update purchase order."
        )



# @router.delete("/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_po(
#     po_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(PurchaseOrder).where(
#             PurchaseOrder.id == po_id,
#             PurchaseOrder.hospital_id == hospital_id,
#             PurchaseOrder.branch_id == branch_id
#         )
#     )
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=404, detail="Purchase Order not found")
#
#     await db.delete(po)
#     await db.commit()
@router.delete("/{po_id}", status_code=status.HTTP_200_OK)
async def delete_po(
    po_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )

    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found"
        )

    await db.delete(po)
    await db.commit()

    return {
        "message": "Purchase Order deleted successfully"
    }

from app.models.vendor import VendorTransaction
from app.utils.vendor_ledger import calculate_vendor_payable

# ------------------ POST PURCHASE TO ACCOUNTS ------------------

@router.post("/{po_id}/post-to-accounts")
async def post_purchase_to_accounts(
    po_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    # Fetch PO
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )
    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Prevent duplicate posting
    if po.is_posted:
        raise HTTPException(
            status_code=400,
            detail="Purchase already posted to accounts"
        )

    # ----------- CALCULATION LOGIC -----------
    subtotal = po.quantity * po.rate

    discount_amount = (subtotal * (po.discount or 0)) / 100
    taxable_amount = subtotal - discount_amount

    gst_amount = (taxable_amount * (po.gst or 0)) / 100

    total_amount = taxable_amount + gst_amount
    # ----------------------------------------

    # Create Ledger Entry (CREDIT)
    transaction = VendorTransaction(
        vendor_id=po.vendor_id,
        hospital_id=hospital_id,
        branch_id=branch_id,
        type="credit",
        amount=total_amount,
        reference=po.po_number,
        notes="PO Posted to Accounts"
    )

    db.add(transaction)

    # Mark as posted
    po.is_posted = True

    await db.commit()

    # Get updated payable
    payable = await calculate_vendor_payable(
        db,
        po.vendor_id,
        hospital_id,
        branch_id
    )

    return {
        "message": "Purchase posted successfully",
        "po_number": po.po_number,
        "total_amount": total_amount,
        "current_payable": payable
    }


@router.post("/vendor/{vendor_id}/pay")
async def pay_vendor(
    vendor_id: int,
    data: VendorPaymentCreate ,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    # Validate vendor
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id
        )
    )
    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Check payable before payment
    # payable = await calculate_vendor_payable(
    #     db, vendor_id, hospital_id, branch_id
    # )
    #
    # if data.amount > payable:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Payment exceeds payable amount"
    #     )
    # Check payable before payment
    payable = await calculate_vendor_payable(
        db,
        vendor_id,
        hospital_id,
        branch_id
    )

    print("PAYABLE =", payable)

    # No payable exists
    if payable <= 0:
        raise HTTPException(
            status_code=400,
            detail="No payable amount for this vendor"
        )

    # Payment exceeds payable
    if data.amount > payable:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum payable amount is {payable}"
        )

    # Create DEBIT entry
    transaction = VendorTransaction(
        vendor_id=vendor_id,
        hospital_id=hospital_id,
        branch_id=branch_id,
        type="debit",
        amount=data.amount,
        reference=data.reference_no,
        notes=data.notes or "Vendor Payment"
    )

    db.add(transaction)
    await db.commit()

    updated_payable = await calculate_vendor_payable(
        db, vendor_id, hospital_id, branch_id
    )

    return {
        "message": "Payment successful",
        "paid_amount": data.amount,
        "remaining_payable": updated_payable
    }

@router.get("/vendor/{vendor_id}/payable")
async def get_vendor_payable(
    vendor_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    payable = await calculate_vendor_payable(
        db, vendor_id, hospital_id, branch_id
    )

    return {
        "vendor_id": vendor_id,
        "payable": payable
    }    

# @router.post("/{po_id}/send-email")
# async def send_po_email(
#     po_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     # Fetch PO
#     result = await db.execute(
#         select(PurchaseOrder).where(
#             PurchaseOrder.id == po_id,
#             PurchaseOrder.hospital_id == hospital_id,
#             PurchaseOrder.branch_id == branch_id
#         )
#     )
#
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=404, detail="PO not found")
#
#     # Fetch Vendor
#     result = await db.execute(
#         select(Vendor).where(
#             Vendor.id == po.vendor_id,
#             Vendor.hospital_id == hospital_id,
#             Vendor.branch_id == branch_id
#         )
#     )
#
#     vendor = result.scalar_one_or_none()
#
#     if not vendor:
#         raise HTTPException(status_code=404, detail="Vendor not found")
#
#     # Email body
#     body = f"""
# Purchase Order
#
# PO Number: {po.po_number}
#
# Medicine ID: {po.medicine_id}
# Quantity: {po.quantity}
# Rate: {po.rate}
# GST: {po.gst}
#
# Delivery Location:
# {po.delivery_location}
#
# Terms:
# {po.terms}
# """
#
#     message = MessageSchema(
#         subject=f"Purchase Order {po.po_number}",
#         recipients=[vendor.email],
#         body=body,
#         subtype="plain"
#     )
#
#     fm = FastMail(conf)
#
#     await fm.send_message(message)
#
#     return {
#         "message": "PO email sent successfully",
#         "vendor_email": vendor.email
#     }

# @router.post("/{po_id}/send-email")
# async def send_po_email(
#     po_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     # FETCH PURCHASE ORDER
#
#     result = await db.execute(
#         select(PurchaseOrder).where(
#             PurchaseOrder.id == po_id,
#             PurchaseOrder.hospital_id == hospital_id,
#             PurchaseOrder.branch_id == branch_id
#         )
#     )
#
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(
#             status_code=404,
#             detail="Purchase Order not found"
#         )
#
#     # FETCH VENDOR
#
#     result = await db.execute(
#         select(Vendor).where(
#             Vendor.id == po.vendor_id,
#             Vendor.hospital_id == hospital_id,
#             Vendor.branch_id == branch_id
#         )
#     )
#
#     vendor = result.scalar_one_or_none()
#
#     if not vendor:
#         raise HTTPException(
#             status_code=404,
#             detail="Vendor not found"
#         )
#
#     if not vendor.email:
#         raise HTTPException(
#             status_code=400,
#             detail="Vendor email not available"
#         )
#
#     # EMAIL BODY
#
#     body = f"""
# PURCHASE ORDER
#
# PO Number: {po.po_number}
#
# Medicine ID: {po.medicine_id}
# Quantity: {po.quantity}
# Rate: {po.rate}
# Discount: {po.discount}
# GST: {po.gst}
#
# Delivery Location:
# {po.delivery_location}
#
# Delivery Deadline:
# {po.delivery_deadline}
#
# Terms:
# {po.terms}
# """
#
#     # CREATE MESSAGE
#
#     message = MessageSchema(
#         subject=f"Purchase Order - {po.po_number}",
#         recipients=[vendor.email],
#         body=body,
#         subtype="plain"
#     )
#
#     fm = FastMail(conf)
#
#     # SEND EMAIL
#
#     try:
#         await fm.send_message(message)
#
#         return {
#             "message": "PO email sent successfully",
#             "vendor_email": vendor.email
#         }
#
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Email sending failed: {str(e)}"
#         )

import asyncio

@router.post("/{po_id}/send-email")
async def send_po_email(
    po_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.id == po_id,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )

    po = result.scalar_one_or_none()

    if not po:
        raise HTTPException(
            status_code=404,
            detail="Purchase Order not found"
        )

    result = await db.execute(
        select(Vendor).where(
            Vendor.id == po.vendor_id,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id
        )
    )

    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    if not vendor.email:
        raise HTTPException(
            status_code=400,
            detail="Vendor email not available"
        )

    body = f"""
PURCHASE ORDER

PO Number: {po.po_number}

Medicine ID: {po.medicine_id}
Quantity: {po.quantity}
Rate: {po.rate}
Discount: {po.discount}
GST: {po.gst}

Delivery Location:
{po.delivery_location}

Delivery Deadline:
{po.delivery_deadline}

Terms:
{po.terms}
"""

    success = await asyncio.to_thread(
        send_email,
        vendor.email,
        f"Purchase Order - {po.po_number}",
        body
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Email sending failed"
        )

    return {
        "message": "PO email sent successfully",
        "vendor_email": vendor.email
    }

@router.get("/vendor/{vendor_id}/payment-notification")
async def payment_notification(
    vendor_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(get_current_user)
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    # Vendor validation
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id
        )
    )

    vendor = result.scalar_one_or_none()

    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Payable calculation
    payable = await calculate_vendor_payable(
        db,
        vendor_id,
        hospital_id,
        branch_id
    )

    return {
        "vendor": vendor.name,
        "email": vendor.email,
        "current_due": payable,
        "status": (
            "PAYMENT_PENDING"
            if payable > 0
            else "CLEAR"
        )
    }
#
# @router.get("/vendor/{vendor_id}/credit-flow")
# async def vendor_credit_flow(
#     vendor_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(get_current_user)
# ):
#     hospital_id = current_user["hospital_id"]
#     branch_id = current_user["branch_id"]
#
#     result = await db.execute(
#         select(VendorTransaction).where(
#             VendorTransaction.vendor_id == vendor_id,
#             VendorTransaction.hospital_id == hospital_id,
#             VendorTransaction.branch_id == branch_id
#         )
#     )
#
#     transactions = result.scalars().all()
#
#     credit_total = 0
#     debit_total = 0
#
#     flow = []
#
#     for txn in transactions:
#
#         if txn.type == "credit":
#             credit_total += txn.amount
#
#         elif txn.type == "debit":
#             debit_total += txn.amount
#
#         balance = credit_total - debit_total
#
#         flow.append({
#             "date": txn.created_at,
#             "type": txn.type,
#             "amount": txn.amount,
#             "reference": txn.reference,
#             "running_balance": balance
#         })
#
#     return {
#         "vendor_id": vendor_id,
#         "total_credit": credit_total,
#         "total_paid": debit_total,
#         "current_payable": credit_total - debit_total,
#         "transactions": flow
#     }
