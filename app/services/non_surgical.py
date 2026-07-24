
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import asc, and_
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select,or_
from app.models.entry_models import NonSurgicalItem, NonSurgicalBatch
from app.schemas.entry_schemas import (
    NonSurgicalItemCreate, NonSurgicalItemUpdate,
    NonSurgicalBatchCreate, NonSurgicalBatchUpdate
)
from app.services.stock_ledger import create_stock_ledger_entry
from datetime import date



# async def calculate_total_value(qty: int, costprice: float, gstpercent: float, discountpercent: float) -> float:
#     base = qty * costprice
#     gst_amount = base * (gstpercent / 100)
#     discount_amount = base * (discountpercent / 100)
#     return base + gst_amount - discount_amount


def calculate_total_value( qty: int,cost_price: float,gst_percent: float,discount_percent: float,) -> Decimal:
    qty = Decimal(qty)
    cost_price = Decimal(str(cost_price))
    gst_percent = Decimal(str(gst_percent))
    discount_percent = Decimal(str(discount_percent))

    # Base value
    base = qty * cost_price

    # Discount first
    discount_amount = (base * discount_percent) / Decimal("100")
    taxable_value = base - discount_amount

    # GST after discount
    gst_amount = (taxable_value * gst_percent) / Decimal("100")

    total = taxable_value + gst_amount

    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

async def create_non_surgical_item(db: AsyncSession,item: NonSurgicalItemCreate,hospital_id: int,branch_id: int,) -> NonSurgicalItem:

    db_item = NonSurgicalItem(
        **item.dict(),
        hospital_id=hospital_id,
        branch_id=branch_id,
    )

    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)

    return db_item


async def get_non_surgical_item(db: AsyncSession,item_id: int,hospital_id: int,branch_id: int,) -> Optional[NonSurgicalItem]:

    result = await db.execute(
        select(NonSurgicalItem).where(
            NonSurgicalItem.id == item_id,
            NonSurgicalItem.hospital_id == hospital_id,
            NonSurgicalItem.branch_id == branch_id,
        )
    )

    return result.scalar_one_or_none()


async def get_non_surgical_items(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
) -> List[NonSurgicalItem]:

    query = select(NonSurgicalItem).where(
        NonSurgicalItem.hospital_id == hospital_id,
        NonSurgicalItem.branch_id == branch_id,
    )

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                NonSurgicalItem.item_code.ilike(term),
                NonSurgicalItem.item_name.ilike(term),
                NonSurgicalItem.item_type.ilike(term),
                NonSurgicalItem.specification.ilike(term),
            )
        )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def update_non_surgical_item(
    db: AsyncSession,
    item_id: int,
    hospital_id: int,
    branch_id: int,
    item_update: NonSurgicalItemUpdate,
):
    item = await get_non_surgical_item(
        db,
        item_id,
        hospital_id,
        branch_id
    )

    if not item:
        return None

    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)

    return item


async def delete_non_surgical_item(db: AsyncSession,item_id: int,hospital_id: int,branch_id: int,) -> bool:

    item = await get_non_surgical_item(db, item_id, hospital_id, branch_id)

    if not item:
        return False

    await db.delete(item)
    await db.commit()

    return True

# async def create_non_surgical_batch_crud(db: AsyncSession, batch: NonSurgicalBatchCreate) -> NonSurgicalBatch:
#     total_value = await calculate_total_value(
#         batch.quantity_received, batch.cost_price, batch.gst_percent, batch.discount_percent
#     )
#     db_obj = NonSurgicalBatch(
#         **batch.dict(),
#         quantity_available=batch.quantity_received,
#         total_value=total_value
#     )
#     db.add(db_obj)
#     await db.commit()
#     await db.refresh(db_obj)
#     await create_stock_ledger_entry(
#         db=db,
#         batch_id=db_obj.id,
#         batch_type="non-surgical batch",
#         transaction_type="RECEIPT",
#         quantity_in=batch.quantity_received,
#         quantity_out=0,
#         balance_qty=batch.quantity_received,
#         transaction_value=total_value,
#         remarks="Non-Surgical Batch Received"
#     )
#     return db_obj

async def create_non_surgical_batch_crud(
    db: AsyncSession,
    batch: NonSurgicalBatchCreate,
    hospital_id: int,
    branch_id: int,
) -> NonSurgicalBatch:

    total_value = batch.quantity_received * batch.cost_price

    db_obj = NonSurgicalBatch(
        **batch.dict(),
        hospital_id=hospital_id,
        branch_id=branch_id,
        quantity_available=batch.quantity_received,
        total_value=total_value,
    )

    db.add(db_obj)

    await db.commit()
    await db.refresh(db_obj)

    await create_stock_ledger_entry(
        db=db,
        hospital_id=hospital_id,
        branch_id=branch_id,
        batch_id=db_obj.id,
        batch_type="NON_SURGICAL",
        transaction_type="RECEIPT",
        quantity_in=batch.quantity_received,
        quantity_out=0,
        balance_qty=batch.quantity_received,
        transaction_value=total_value,
        reference_id=db_obj.id,
        remarks="Non-Surgical Batch Received",
    )

    return db_obj

# async def get_fefo_non_surgical_batch(db: AsyncSession, item_id: int, required_qty: int) -> NonSurgicalBatch | None:
#     result = await db.execute(
#         select(NonSurgicalBatch)
#         .where(
#             NonSurgicalBatch.non_surgical_item_id == item_id,
#             NonSurgicalBatch.quantity_available >= required_qty
#         )
#         .order_by(asc(NonSurgicalBatch.expiry_date))
#         .limit(1)
#     )
#     return result.scalar_one_or_none()


# Fix get_fefo_non_surgical_batches
async def get_fefo_non_surgical_batches(
    db: AsyncSession,
    non_surgical_item_id: int,
    quantity: int,
    hospital_id: int,
    branch_id: int
) -> NonSurgicalBatch | None:
    result = await db.execute(
        select(NonSurgicalBatch)
        .where(
            and_(
                NonSurgicalBatch.non_surgical_item_id == non_surgical_item_id,
                NonSurgicalBatch.hospital_id == hospital_id,
                NonSurgicalBatch.branch_id == branch_id,
                NonSurgicalBatch.quantity_available >= quantity,
                or_(
                    NonSurgicalBatch.expiry_date >= date.today(),
                    NonSurgicalBatch.expiry_date.is_(None)  # non-surgical may have no expiry
                ),
            )
        )
        .order_by(NonSurgicalBatch.expiry_date.asc())
    )
    return result.scalars().first()

async def update_non_surgical_batch_quantity(db: AsyncSession, batch_id: int, new_qty: int) -> NonSurgicalBatch | None:
    result = await db.execute(
        select(NonSurgicalBatch).where(NonSurgicalBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if batch:
        batch.quantity_available = new_qty
        await db.commit()
        await db.refresh(batch)
    return batch



async def get_non_surgical_batch(
    db: AsyncSession,
    *,
    batch_id: int,
    hospital_id: int,
    branch_id: int,
):

    result = await db.execute(
        select(NonSurgicalBatch).where(
            NonSurgicalBatch.id == batch_id,
            NonSurgicalBatch.hospital_id == hospital_id,
            NonSurgicalBatch.branch_id == branch_id,
        )
    )

    return result.scalar_one_or_none()

async def get_non_surgical_batches(
    db: AsyncSession,
    *,
    hospital_id: int,
    branch_id: int,
    skip: int = 0,
    limit: int = 100,
    non_surgical_item_id: Optional[int] = None,
):

    query = select(NonSurgicalBatch).where(
        NonSurgicalBatch.hospital_id == hospital_id,
        NonSurgicalBatch.branch_id == branch_id,
    )

    if non_surgical_item_id:
        query = query.where(
            NonSurgicalBatch.non_surgical_item_id == non_surgical_item_id
        )

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


async def update_non_surgical_batch(
    db: AsyncSession,
    batch_id: int,
    batch_update: NonSurgicalBatchUpdate,
    hospital_id: int,
    branch_id: int,
):
    batch = await get_non_surgical_batch(
        db=db,
        batch_id=batch_id,
        hospital_id=hospital_id,
        branch_id=branch_id,
    )

    if not batch:
        return None

    for field, value in batch_update.dict(exclude_unset=True).items():
        setattr(batch, field, value)

    await db.commit()
    await db.refresh(batch)

    return batch


async def delete_non_surgical_batch_db(
    db: AsyncSession,
    batch_id: int,
    hospital_id: int,
    branch_id: int,
):

    batch = await get_non_surgical_batch(
        db=db,
        batch_id=batch_id,
        hospital_id=hospital_id,
        branch_id=branch_id,
    )

    if not batch:
        return False

    await db.delete(batch)
    await db.commit()

    return True