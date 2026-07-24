from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import or_
from app.models.entry_models import SurgicalItem, SurgicalBatch
from app.schemas.entry_schemas import (
    SurgicalItemCreate, SurgicalItemUpdate,
    SurgicalBatchCreate, SurgicalBatchUpdate
)
from app.services.stock_ledger import create_stock_ledger_entry
from datetime import date



async def calculate_total_value(qty: int, costprice: float, gstpercent: float, discountpercent: float) -> float:
    base = qty * costprice
    gst_amount = base * (gstpercent / 100)
    discount_amount = base * (discountpercent / 100)
    return base + gst_amount - discount_amount


async def create_surgical_item(db: AsyncSession, item: SurgicalItemCreate) -> SurgicalItem:
    db_obj = SurgicalItem(**item.dict())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_surgical_item(db: AsyncSession, item_id: int) -> SurgicalItem | None:
    result = await db.execute(select(SurgicalItem).where(SurgicalItem.id == item_id))
    return result.scalar_one_or_none()


async def get_surgical_items(db: AsyncSession, skip: int = 0, limit: int = 100,
                             search: Optional[str] = None) -> list[SurgicalItem]:
    query = select(SurgicalItem).offset(skip).limit(limit)
    if search:
        query = query.where(
            or_(
                SurgicalItem.item_name.ilike(f"%{search}%"),
                SurgicalItem.item_code.ilike(f"%{search}%")
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


async def create_surgical_batch(
    db: AsyncSession,
    batch: SurgicalBatchCreate
) -> SurgicalBatch:

    total_value = await calculate_total_value(
        batch.quantity_received,
        batch.cost_price,
        batch.gst_percent,
        batch.discount_percent
    )

    db_obj = SurgicalBatch(
        **batch.dict(),
        quantity_available=batch.quantity_received,
        total_value=total_value
    )

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    # await create_stock_ledger_entry(
    #     db=db,
    #     batch_id=db_obj.id,
    #     batch_type="surgical",
    #     transaction_type="RECEIPT",
    #     qty_in=batch.quantity_received,
    #     qty_out=0,
    #     balance_qty=batch.quantity_received,
    #     trans_value=total_value,
    #     remarks="Surgical Batch Received"
    # )
    await create_stock_ledger_entry(
    db=db,
    hospital_id=batch.hospital_id,
    branch_id=batch.branch_id,
    batch_id=db_obj.id,
    batch_type="SURGICAL_BATCH",
    transaction_type="RECEIPT",
    quantity_in=batch.quantity_received,
    quantity_out=0,
    balance_qty=batch.quantity_received,
    transaction_value=total_value,
    reference_id=db_obj.id,
    remarks="Surgical Batch Received"
)

    return db_obj

async def get_fefo_surgical_batch(
    db: AsyncSession,
    surgical_item_id: int,
    quantity: int,
    hospital_id: int,
    branch_id: int
) -> SurgicalBatch | None:
    result = await db.execute(
        select(SurgicalBatch)
        .where(
            and_(
                SurgicalBatch.surgical_item_id == surgical_item_id,
                SurgicalBatch.hospital_id == hospital_id,
                SurgicalBatch.branch_id == branch_id,
                SurgicalBatch.quantity_available >= quantity,
                or_(
                    SurgicalBatch.expiry_date >= date.today(),
                    SurgicalBatch.expiry_date.is_(None)  # surgical may have no expiry
                ),
            )
        )
        .order_by(SurgicalBatch.expiry_date.asc())
    )
    return result.scalars().first()


async def update_surgical_batch_quantity(db: AsyncSession, batch_id: int, new_qty: int) -> SurgicalBatch | None:
    result = await db.execute(select(SurgicalBatch).where(SurgicalBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if batch:
        batch.quantity_available = new_qty
        await db.commit()
        await db.refresh(batch)
    return batch


#

async def update_surgical_item(db: AsyncSession, item_id: int,
                               item_update: SurgicalItemUpdate) -> SurgicalItem | None:
    """Update surgical item details"""
    item = await get_surgical_item(db, item_id)
    if not item:
        return None

    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


async def delete_surgical_item(db: AsyncSession, item_id: int) -> bool:
    """Delete surgical item"""
    item = await get_surgical_item(db, item_id)
    if not item:
        return False

    await db.delete(item)
    await db.commit()
    return True


async def get_surgical_batch(db: AsyncSession, batch_id: int) -> SurgicalBatch | None:
    """Get single surgical batch by ID"""
    result = await db.execute(select(SurgicalBatch).where(SurgicalBatch.id == batch_id))
    return result.scalar_one_or_none()


async def get_surgical_batches(db: AsyncSession, skip: int = 0, limit: int = 100,
                               surgical_item_id: Optional[int] = None) -> List[SurgicalBatch]:
    """List surgical batches with optional item filtering"""
    query = select(SurgicalBatch).offset(skip).limit(limit)
    if surgical_item_id:
        query = query.where(SurgicalBatch.surgical_item_id == surgical_item_id)
    result = await db.execute(query)
    return result.scalars().all()


async def update_surgical_batch(db: AsyncSession, batch_id: int,
                                batch_update: SurgicalBatchUpdate) -> SurgicalBatch | None:
    """Update surgical batch details"""
    batch = await get_surgical_batch(db, batch_id)
    if not batch:
        return None

    update_data = batch_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(batch, field, value)

    await db.commit()
    await db.refresh(batch)
    return batch


async def delete_surgical_batch(db: AsyncSession, batch_id: int) -> bool:
    """Delete surgical batch"""
    batch = await get_surgical_batch(db, batch_id)
    if not batch:
        return False

    await db.delete(batch)
    await db.commit()
    return True
