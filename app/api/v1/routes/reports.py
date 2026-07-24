# from fastapi import APIRouter, Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from app.database import get_db
# from app.models.entry_models import Medicine, Batch, StockLedger

# router = APIRouter(prefix="/reports", tags=["reports"])


# # @router.get("/expiry-list")
# # async def expiry_list(db: AsyncSession = Depends(get_db)):
# #
# #     today = date.today()
# #     result = await db.execute(
# #         select(Batch, Medicine)
# #         .join(Medicine, Batch.medicine_id == Medicine.id)
# #         .where(Batch.quantity_available > 0)
# #     )
# #
# #     batches_medicines = result.all()
# #     return [
# #         {
# #             "medicine_name": medicine.item_name,
# #             "batch_no": batch.batch_number,
# #             "qty": batch.quantity_available,
# #             "mfg_date": batch.manufacture_date,
# #             "expiry_date": batch.expiry_date,
# #             "days_to_expire": (batch.expiry_date - today).days
# #         }
# #         for batch, medicine in batches_medicines
# #     ]

# from collections import defaultdict
# from sqlalchemy import func
# from datetime import date
# from sqlalchemy import and_


# @router.get("/expiry-list")
# async def expiry_list(db: AsyncSession = Depends(get_db)):
#     today = date.today()
#     result = await db.execute(
#         select(Batch, Medicine)
#         .join(Medicine, Batch.medicine_id == Medicine.id)
#         .where(Batch.quantity_available > 0)
#         .order_by(Batch.expiry_date.asc())
#     )

#     batches_medicines = result.all()

#     # Group by medicine + batch_number to consolidate quantities
#     batch_summary = defaultdict(int)
#     expiry_details = {}

#     for batch, medicine in batches_medicines:
#         key = (medicine.item_name, batch.batch_number)
#         batch_summary[key] += batch.quantity_available

#         # Store expiry info(take earliest expiry)
#         if key not in expiry_details or batch.expiry_date < expiry_details[key]['expiry_date']:
#             expiry_details[key] = {
#                 'mfg_date': batch.manufacture_date,
#                 'expiry_date': batch.expiry_date
#             }

#     #final response
#     return [
#         {
#             "medicine_name": medicine_name,
#             "batch_no": batch_no,
#             "qty": total_qty,
#             "mfg_date": expiry_details[key]['mfg_date'].isoformat() if expiry_details[key]['mfg_date'] else None,
#             "expiry_date": expiry_details[key]['expiry_date'].isoformat() if expiry_details[key][
#                 'expiry_date'] else None,
#             "days_to_expire": (expiry_details[key]['expiry_date'] - today).days if expiry_details[key][
#                 'expiry_date'] else None
#         }
#         for (medicine_name, batch_no), total_qty in batch_summary.items()
#     ]


# # @router.get("/stock-summary")
# # async def stock_summary(db: AsyncSession = Depends(get_db)):
# #     result = await db.execute(
# #         future_select(
# #             StockLedger.batch_id,
# #             func.sum(StockLedger.quantity_in).label("total_in"),
# #             func.sum(StockLedger.quantity_out).label("total_out"),
# #             func.sum(StockLedger.balance_qty).label("closing")
# #         )
# #         .group_by(StockLedger.batch_id)
# #     )
# #
# #
# #     rows = result.fetchall()
# #
# #     return [
# #         {
# #             "batch_id": row[0],
# #             "opening_stock": 0,
# #             "received_stock": row[1] or 0,
# #             "issued_stock": row[2] or 0,
# #             "closing_stock": row[3] or 0
# #         }
# #         for row in rows
# #     ]

# @router.get("/stock-summary")
# async def stock_summary(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(
#         select(
#             StockLedger.batch_id,
#             func.coalesce(func.min(StockLedger.quantity_in), 0).label("opening_stock"),
#             func.coalesce(func.sum(StockLedger.quantity_in), 0).label("received_stock"),
#             func.coalesce(func.sum(StockLedger.quantity_out), 0).label("issued_stock"),
#             func.coalesce(func.sum(StockLedger.balance_qty), 0).label("closing_stock")
#         )
#         .group_by(StockLedger.batch_id)
#         .order_by(StockLedger.batch_id)
#     )

#     rows = result.fetchall()

#     batch_details = {}
#     for row in rows:
#         batch_id = row[0]
#         if batch_id not in batch_details:
#             batch_result = await db.execute(
#                 select(Batch.batch_number, Medicine.item_name)
#                 .join(Medicine, Batch.medicine_id == Medicine.id)
#                 .where(Batch.id == batch_id)
#             )
#             batch_info = batch_result.fetchone()
#             batch_details[batch_id] = {
#                 "batch_no": batch_info[0] if batch_info else f"Batch-{batch_id}",
#                 "medicine_name": batch_info[1] if batch_info else "Unknown"
#             }

#     return [
#         {
#             "batch_id": row[0],
#             "medicine_name": batch_details[row[0]]["medicine_name"],
#             "batch_no": batch_details[row[0]]["batch_no"],
#             "opening_stock": row[1],
#             "received_stock": row[2],
#             "issued_stock": row[3],
#             "closing_stock": row[4]
#         }
#         for row in rows
#     ]



# @router.get("/expired-stock")
# async def expired_stock(db: AsyncSession = Depends(get_db)):
#     today = date.today()
#     result = await db.execute(
#         select(Batch, Medicine)
#         .join(Medicine, Batch.medicine_id == Medicine.id)
#         .where(
#             and_(
#                 Batch.expiry_date < today,
#                 Batch.quantity_available > 0
#             )
#         )
#         .order_by(Batch.expiry_date.asc())
#     )

#     expired_batches = result.all()
#     total_qty = sum(batch.quantity_available for batch, _ in expired_batches)

#     return {
#         "expired_quantity": total_qty,
#         "expired_batches": len(expired_batches),
#         "total_value_lost": 0,
#         "details": [
#             {
#                 "batch_id": batch.id,
#                 "medicine_name": medicine.item_name,
#                 "batch_number": batch.batch_number,
#                 "quantity": batch.quantity_available,
#                 "expiry_date": batch.expiry_date.isoformat(),
#                 "days_overdue": (today - batch.expiry_date).days
#             }
#             for batch, medicine in expired_batches
#         ]
#     }



# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func, and_
# from datetime import date

# from app.database import get_db
# from app.models.entry_models import Medicine, Batch, StockLedger

# router = APIRouter(prefix="/reports", tags=["Reports"])


# @router.get("/expiry-list")
# async def expiry_list(
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     db: AsyncSession = Depends(get_db)
# ):
#     today = date.today()

#     result = await db.execute(
#         select(
#             Medicine.item_name,
#             Batch.batch_number,
#             Batch.manufacture_date,
#             Batch.expiry_date,
#             func.sum(Batch.quantity_available).label("total_qty")
#         )
#         .join(Medicine, Batch.medicine_id == Medicine.id)
#         .where(
#             and_(
#                 Batch.quantity_available > 0,
#                 Batch.hospital_id == hospital_id,
#                 Batch.branch_id == branch_id
#             )
#         )
#         .group_by(
#             Medicine.item_name,
#             Batch.batch_number,
#             Batch.manufacture_date,
#             Batch.expiry_date
#         )
#         .order_by(Batch.expiry_date.asc())
#     )

#     rows = result.fetchall()

#     return [
#         {
#             "medicine_name": r.item_name,
#             "batch_no": r.batch_number,
#             "qty": r.total_qty,
#             "mfg_date": r.manufacture_date.isoformat()
#             if r.manufacture_date else None,
#             "expiry_date": r.expiry_date.isoformat()
#             if r.expiry_date else None,
#             "days_to_expire": (r.expiry_date - today).days
#             if r.expiry_date else None
#         }
#         for r in rows
#     ]


# @router.get("/stock-summary")
# async def stock_summary(
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     db: AsyncSession = Depends(get_db)
# ):

#     result = await db.execute(
#         select(
#             StockLedger.batch_id,
#             Medicine.item_name,
#             Batch.batch_number,

#             func.coalesce(func.sum(StockLedger.quantity_in), 0)
#             .label("received_stock"),

#             func.coalesce(func.sum(StockLedger.quantity_out), 0)
#             .label("issued_stock"),

#             func.coalesce(func.max(StockLedger.balance_qty), 0)
#             .label("closing_stock"),
#         )
#         .join(Batch, Batch.id == StockLedger.batch_id)
#         .join(Medicine, Medicine.id == Batch.medicine_id)
#         .where(
#             and_(
#                 StockLedger.hospital_id == hospital_id,
#                 StockLedger.branch_id == branch_id
#             )
#         )
#         .group_by(
#             StockLedger.batch_id,
#             Medicine.item_name,
#             Batch.batch_number
#         )
#         .order_by(StockLedger.batch_id)
#     )

#     rows = result.fetchall()

#     return [
#         {
#             "batch_id": r.batch_id,
#             "medicine_name": r.item_name,
#             "batch_no": r.batch_number,
#             "opening_stock": 0,
#             "received_stock": r.received_stock,
#             "issued_stock": r.issued_stock,
#             "closing_stock": r.closing_stock,
#         }
#         for r in rows
#     ]

# @router.get("/expired-stock")
# async def expired_stock(
#     hospital_id: int = Query(...),
#     branch_id: int = Query(...),
#     db: AsyncSession = Depends(get_db)
# ):

#     today = date.today()

#     result = await db.execute(
#         select(
#             Batch.id,
#             Medicine.item_name,
#             Batch.batch_number,
#             Batch.quantity_available,
#             Batch.expiry_date
#         )
#         .join(Medicine, Batch.medicine_id == Medicine.id)
#         .where(
#             and_(
#                 Batch.expiry_date < today,
#                 Batch.quantity_available > 0,
#                 Batch.hospital_id == hospital_id,
#                 Batch.branch_id == branch_id
#             )
#         )
#         .order_by(Batch.expiry_date.asc())
#     )

#     rows = result.fetchall()

#     total_qty = sum(r.quantity_available for r in rows)

#     return {
#         "expired_quantity": total_qty,
#         "expired_batches": len(rows),
#         "total_value_lost": 0,
#         "details": [
#             {
#                 "batch_id": r.id,
#                 "medicine_name": r.item_name,
#                 "batch_number": r.batch_number,
#                 "quantity": r.quantity_available,
#                 "expiry_date": r.expiry_date.isoformat(),
#                 "days_overdue": (today - r.expiry_date).days
#             }
#             for r in rows
#         ]
#     }


from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
# from app.models.auth import User
# from app.core.security import (
#     async_get_db,
#     get_current_user,
#     require_roles
# )
from app.core.security import async_get_db, require_roles, get_current_user
from app.models.auth import User
from app.models.entry_models import Medicine, Batch, StockLedger

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(require_roles("superadmin","pharmacist"))]
)


# EXPIRY LIST (WITH ALERTS)
@router.get("/expiry-list")
async def expiry_list(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    alert_days: int = Query(None),  # 30 / 60 / 90
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()

    conditions = [
        Batch.quantity_available > 0,
        Batch.hospital_id == hospital_id,
        Batch.branch_id == branch_id
    ]

    if alert_days:
        conditions.append(Batch.expiry_date <= today + timedelta(days=alert_days))

    result = await db.execute(
        select(
            Batch.id,
            Medicine.item_name,
            Batch.batch_number,
            Batch.manufacture_date,
            Batch.expiry_date,
            Batch.quantity_available
        )
        .join(Medicine, Batch.medicine_id == Medicine.id)
        .where(and_(*conditions))
        .order_by(Batch.expiry_date.asc())
    )

    rows = result.fetchall()

    def get_status(expiry_date):
        days = (expiry_date - today).days
        if days < 0:
            return "EXPIRED"
        elif days <= 30:
            return "NEAR_EXPIRY"
        else:
            return "SAFE"

    return [
        {
            "batch_id": r.id,
            "medicine_name": r.item_name,
            "batch_no": r.batch_number,
            "qty": r.quantity_available,
            "mfg_date": r.manufacture_date.isoformat(),
            "expiry_date": r.expiry_date.isoformat(),
            "days_to_expire": (r.expiry_date - today).days,
            "status": get_status(r.expiry_date),
            "is_blocked": (r.expiry_date - today).days <= 30
        }
        for r in rows
    ]



# STOCK SUMMARY
@router.get("/stock-summary")
async def stock_summary(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db)
):
    today = date.today()

    result = await db.execute(
        select(
            StockLedger.batch_id,
            Medicine.item_name,
            Batch.batch_number,
            Batch.expiry_date,

            func.coalesce(func.sum(StockLedger.quantity_in), 0).label("received_stock"),
            func.coalesce(func.sum(StockLedger.quantity_out), 0).label("issued_stock"),
            func.coalesce(func.max(StockLedger.balance_qty), 0).label("closing_stock"),
        )
        .join(Batch, Batch.id == StockLedger.batch_id)
        .join(Medicine, Medicine.id == Batch.medicine_id)
        .where(
            and_(
                StockLedger.hospital_id == hospital_id,
                StockLedger.branch_id == branch_id
            )
        )
        .group_by(
            StockLedger.batch_id,
            Medicine.item_name,
            Batch.batch_number,
            Batch.expiry_date
        )
        .order_by(StockLedger.batch_id)
    )

    rows = result.fetchall()

    return [
        {
            "batch_id": r.batch_id,
            "medicine_name": r.item_name,
            "batch_no": r.batch_number,
            "received_stock": r.received_stock,
            "issued_stock": r.issued_stock,
            "closing_stock": r.closing_stock,
            "expiry_date": r.expiry_date.isoformat(),
            "days_to_expire": (r.expiry_date - today).days,
            "is_blocked": (r.expiry_date - today).days <= 30,
            "is_expired": r.expiry_date < today
        }
        for r in rows
    ]



# EXPIRED STOCK + LOSS
@router.get("/expired-stock")
async def expired_stock(
    hospital_id: int = Query(...),
    branch_id: int = Query(...),
    db: AsyncSession = Depends(async_get_db)
):
    today = date.today()

    result = await db.execute(
        select(
            Batch.id,
            Medicine.item_name,
            Batch.batch_number,
            Batch.quantity_available,
            Batch.expiry_date,
            Batch.cost_price
        )
        .join(Medicine, Batch.medicine_id == Medicine.id)
        .where(
            and_(
                Batch.expiry_date < today,
                Batch.quantity_available > 0,
                Batch.hospital_id == hospital_id,
                Batch.branch_id == branch_id
            )
        )
        .order_by(Batch.expiry_date.asc())
    )

    rows = result.fetchall()

    total_qty = sum(r.quantity_available for r in rows)

    total_loss = sum(
        r.quantity_available * (r.cost_price or 0)
        for r in rows
    )

    return {
        "expired_quantity": total_qty,
        "expired_batches": len(rows),
        "total_value_lost": total_loss,
        "details": [
            {
                "batch_id": r.id,
                "medicine_name": r.item_name,
                "batch_number": r.batch_number,
                "quantity": r.quantity_available,
                "expiry_date": r.expiry_date.isoformat(),
                "days_overdue": (today - r.expiry_date).days,
                "cost_price": r.cost_price,
                "loss_value": r.quantity_available * (r.cost_price or 0)
            }
            for r in rows
        ]
    }



# RETURN TO VENDOR
@router.post("/return-to-vendor")
async def return_to_vendor(
    batch_id: int,
    quantity: int,
    hospital_id: int,
    branch_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user)
):
    batch = await db.get(Batch, batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    if batch.quantity_available < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # days = (batch.expiry_date - date.today()).days
    #
    # if days > 30:
    #     raise HTTPException(status_code=400, detail="Only near-expiry or expired stock can be returned")

    batch.quantity_available -= quantity
    batch.returned_quantity += quantity

    ledger = StockLedger(
        batch_id=batch_id,
        batch_type="medicine",
        hospital_id=hospital_id,
        branch_id=branch_id,
        transaction_type="RETURN_TO_VENDOR",
        quantity_in=0,
        quantity_out=quantity,
        balance_qty=batch.quantity_available,
        transaction_value=quantity * (batch.cost_price or 0),  # ← added value
        remarks=f"Returned to vendor - batch {batch.batch_number}",  # ← added remarks
    )

    db.add(ledger)
    await db.commit()

    return {"message": "Returned to vendor successfully"}