# routers/grn.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pymysql import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import async_get_db
from app.models.grn import GRN, GRNItem
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder
from app.schemas.grn import GRNCreate, GRNOut
from app.schemas.vendor import VendorRating
from app.core.security import require_roles

router = APIRouter(prefix="/grn", tags=["GRN"])


# @router.post("/", response_model=GRNOut, status_code=status.HTTP_201_CREATED)
# async def create_grn(
#     data: GRNCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
# ):
#     hospital_id = current_user["hospital_id"]
#     branch_id = current_user["branch_id"]
#
#     # ---------------- Vendor Check ----------------
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
#         raise HTTPException(400, "Invalid vendor")
#
#     if vendor.rating == VendorRating.BLACKLISTED:
#         raise HTTPException(400, "Blacklisted vendor cannot supply goods")
#
#     # ---------------- PO Check ----------------
#     result = await db.execute(
#         select(PurchaseOrder).where(
#             PurchaseOrder.id == data.po_id,
#             PurchaseOrder.hospital_id == hospital_id,
#             PurchaseOrder.branch_id == branch_id
#         )
#     )
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(400, "Invalid PO")
#
#     # ---------------- Create GRN ----------------
#     grn = GRN(
#         grn_number=f"GRN-{data.po_id}",
#         vendor_id=data.vendor_id,
#         po_id=data.po_id,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         invoice_number=data.invoice_number,
#         received_by=data.received_by,
#         remarks=data.remarks
#     )
#
#     db.add(grn)
#     await db.flush()
#
#     # ---------------- Items ----------------
#     for item in data.items:
#
#         if item.received_qty > item.ordered_qty:
#             raise HTTPException(400, "Received qty cannot exceed ordered qty")
#
#         if item.damaged_qty > item.received_qty:
#             raise HTTPException(400, "Damaged qty cannot exceed received qty")
#
#         db.add(GRNItem(
#             grn_id=grn.id,
#             **item.model_dump()
#         ))
#
#     await db.commit()
#     await db.refresh(grn)
#
#     return grn
#
# @router.post("/", response_model=GRNOut, status_code=201)
# async def create_grn(
#     data: GRNCreate,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     # ---------------- Vendor Check ----------------
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
#         raise HTTPException(status_code=400, detail="Invalid vendor")
#
#     if vendor.status and vendor.status.lower() == "blacklisted":
#         raise HTTPException(status_code=400, detail="Vendor is blacklisted")
#
#     # ---------------- PO Check (FIXED) ----------------
#     result = await db.execute(
#         select(PurchaseOrder).where(
#             PurchaseOrder.po_number == data.po_id,
#             PurchaseOrder.hospital_id == hospital_id,
#             PurchaseOrder.branch_id == branch_id
#         )
#     )
#
#     po = result.scalar_one_or_none()
#
#     if not po:
#         raise HTTPException(status_code=400, detail="Invalid PO")
#
#     # ---------------- GRN CREATE ----------------
#     grn = GRN(
#         grn_number=f"GRN-{po.po_number}",
#         vendor_id=data.vendor_id,
#         po_id=po.id,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         invoice_number=data.invoice_number,
#         received_by=data.received_by,
#         remarks=data.remarks
#     )
#
#     db.add(grn)
#     await db.flush()
#
#     # ---------------- ITEMS ----------------
#     for item in data.items:
#
#         if item.received_qty > item.ordered_qty:
#             raise HTTPException(400, "Received qty cannot exceed ordered qty")
#
#         if item.damaged_qty > item.received_qty:
#             raise HTTPException(400, "Damaged qty cannot exceed received qty")
#
#         db.add(GRNItem(
#             grn_id=grn.id,
#             medicine_id=item.medicine_id,
#             ordered_qty=item.ordered_qty,
#             received_qty=item.received_qty,
#             damaged_qty=item.damaged_qty,
#             batch_number=item.batch_number,
#             expiry_date=item.expiry_date
#         ))
#
#     await db.commit()
#     await db.refresh(grn)
#
#     return grn

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_grn(
    data: GRNCreate,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    # ---------------- VENDOR CHECK ----------------
    vendor_res = await db.execute(
        select(Vendor).where(
            Vendor.id == data.vendor_id,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id
        )
    )
    vendor = vendor_res.scalar_one_or_none()

    if not vendor:
        raise HTTPException(400, "Invalid vendor")

    if (vendor.status or "").lower() == "blacklisted":
        raise HTTPException(400, "Vendor is blacklisted")

    # ---------------- PO CHECK (FIXED) ----------------

    print("Searching PO:", data.po_id)
    print("Hospital:", hospital_id)
    print("Branch:", branch_id)

    po_res = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.po_number == data.po_id,
            PurchaseOrder.hospital_id == hospital_id,
            PurchaseOrder.branch_id == branch_id
        )
    )
    po = po_res.scalar_one_or_none()

    print("PO Found:", po)

    if not po:
        raise HTTPException(400, "Invalid PO")

    # ---------------- UNIQUE GRN NUMBER ----------------
    grn_number = f"GRN-{data.po_id}-{int(datetime.utcnow().timestamp())}"

    # ---------------- CREATE GRN ----------------
    grn = GRN(
        grn_number=grn_number,
        vendor_id=data.vendor_id,
        po_id=po.id,
        hospital_id=hospital_id,
        branch_id=branch_id,
        invoice_number=data.invoice_number,
        received_by=data.received_by,
        remarks=data.remarks,
        received_date=datetime.utcnow()
    )

    db.add(grn)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            400,
            "GRN number already exists, retry request"
        )

    # ---------------- ITEMS ----------------
    for item in data.items:

        if item.received_qty > item.ordered_qty:
            raise HTTPException(400, "Received qty cannot exceed ordered qty")

        if item.damaged_qty > item.received_qty:
            raise HTTPException(400, "Damaged qty cannot exceed received qty")

        db.add(GRNItem(
            grn_id=grn.id,
            medicine_id=item.medicine_id,
            ordered_qty=item.ordered_qty,
            received_qty=item.received_qty,
            damaged_qty=item.damaged_qty,
            batch_number=item.batch_number,
            expiry_date=item.expiry_date
        ))

    await db.commit()

    # ---------------- SAFE RESPONSE (NO LAZY LOAD) ----------------
    return {
        "id": grn.id,
        "grn_number": grn.grn_number,
        "vendor_id": grn.vendor_id,
        "po_id": po.po_number,
        "hospital_id": hospital_id,
        "branch_id": branch_id,
        "message": "GRN created successfully"
    }

# @router.get("/", response_model=list[GRNOut])
# async def list_grns(
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
# ):
#     hospital_id = current_user.hospital_id
#     branch_id = current_user.branch_id
#
#     result = await db.execute(
#         select(GRN).where(
#             GRN.hospital_id == hospital_id,
#             GRN.branch_id == branch_id
#         )
#     )
#
#     return result.scalars().unique().all()


@router.get("/")
async def list_grns(
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(GRN)
        .where(
            GRN.hospital_id == hospital_id,
            GRN.branch_id == branch_id
        )
        .options(selectinload(GRN.items))
    )

    grns = result.scalars().all()

    response = []

    for grn in grns:

        # get PO safely
        po = await db.get(PurchaseOrder, grn.po_id)

        response.append({
            "id": grn.id,
            "grn_number": grn.grn_number,
            "vendor_id": grn.vendor_id,

            # return string
            "po_id": po.po_number if po else str(grn.po_id),

            "invoice_number": grn.invoice_number,
            "received_by": grn.received_by,
            "remarks": grn.remarks,
            "items": [
                {
                    "id": item.id,
                    "medicine_id": item.medicine_id,
                    "ordered_qty": item.ordered_qty,
                    "received_qty": item.received_qty,
                    "damaged_qty": item.damaged_qty,
                    "batch_number": item.batch_number,
                    "expiry_date": item.expiry_date
                }
                for item in grn.items
            ]
        })

    return response

#
# @router.get("/{grn_id}", response_model=GRNOut)
# async def get_grn(
#     grn_id: int,
#     db: AsyncSession = Depends(get_db),
#     current_user=Depends(role_required(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
# ):
#     result = await db.execute(select(GRN).where(GRN.id == grn_id))
#     grn = result.scalar_one_or_none()
#
#     if not grn:
#         raise HTTPException(404, "GRN not found")
#
#     return grn

@router.get("/{grn_id}", response_model=GRNOut)
async def get_grn(
    grn_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user=Depends(require_roles(["ADMIN", "PHARMACIST", "SUPERADMIN"]))
):
    hospital_id = current_user.hospital_id
    branch_id = current_user.current_branch_id

    result = await db.execute(
        select(GRN)
        .options(selectinload(GRN.items))
        .where(
            GRN.id == grn_id,
            GRN.hospital_id == hospital_id,
            GRN.branch_id == branch_id
        )
    )

    grn = result.scalar_one_or_none()

    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")

    # ---------------- FIX PO TYPE ISSUE ----------------
    po_number = None

    if grn.po_id:
        po = await db.get(PurchaseOrder, grn.po_id)
        po_number = po.po_number if po else str(grn.po_id)

    # ---------------- SAFE MANUAL RESPONSE ----------------
    return {
        "id": grn.id,
        "grn_number": grn.grn_number,
        "vendor_id": grn.vendor_id,

        # ALWAYS STRING (matches GRNOut)
        "po_id": po_number,
        "received_date": grn.received_date,

        "invoice_number": grn.invoice_number,
        "received_by": grn.received_by,
        "remarks": grn.remarks,
        "hospital_id": grn.hospital_id,
        "branch_id": grn.branch_id,

        # NO LAZY ORM ACCESS ISSUE
        "items": [
            {
                "id": item.id,
                "medicine_id": item.medicine_id,
                "ordered_qty": item.ordered_qty,
                "received_qty": item.received_qty,
                "damaged_qty": item.damaged_qty,
                "batch_number": item.batch_number,
                "expiry_date": item.expiry_date
            }
            for item in grn.items
        ]
    }