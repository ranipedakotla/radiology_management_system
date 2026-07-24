from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.entry_models import Medicine, Batch
from app.models.user_models import Sale, SaleItem


async def get_medicine(db: AsyncSession, medicine_id: int):
    return await db.get(Medicine, medicine_id)

async def get_fefo_batch(
    db: AsyncSession,
    medicine_id: int,
    quantity: int,
    hospital_id: int,
    branch_id: int
) -> Batch | None:
    result = await db.execute(
        select(Batch)
        .where(
            and_(
                Batch.medicine_id == medicine_id,
                Batch.hospital_id == hospital_id,
                Batch.branch_id == branch_id,
                Batch.quantity_available >= quantity,  # ← correct column name
                Batch.expiry_date >= date.today(),     # ← skip expired batches
            )
        )
        .order_by(Batch.expiry_date.asc())  # FEFO - oldest expiry first
    )
    return result.scalars().first()

async def create_sale(
    db: AsyncSession,
    payment_mode: str,
    prescription_id: int | None
):
    sale = Sale(
        payment_mode=payment_mode,
        prescription_id=prescription_id,
        total_amount=0
    )
    db.add(sale)
    await db.flush()
    return sale

async def add_sale_item(
    db: AsyncSession,
    sale_id: int,
    medicine_id: int,
    batch_id: int,
    quantity: int,
    price: float
):
    sale_item = SaleItem(
        sale_id=sale_id,
        medicine_id=medicine_id,
        batch_id=batch_id,
        quantity=quantity,
        price=price
    )
    db.add(sale_item)
    return sale_item
