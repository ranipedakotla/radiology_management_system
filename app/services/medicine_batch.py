# from typing import List, Optional
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, asc, or_
# from sqlalchemy.orm import selectinload
# from datetime import date

# from app.models.entry_models import Batch, Medicine
# from app.schemas.entry_schemas import BatchCreate, BatchUpdate
# from app.crud.stock_ledger import create_stock_ledger_entry



# async def calculate_total_value(
#     qty: int,
#     cost_price: float,
#     gst_percent: float,
#     discount_percent: float,
#     cgst_percent: float,
#     sgst_percent: float,
#     min_discount_percent: float = 0.0,
#     max_discount_percent: float = 100.0,
# ) -> float:

#     base = qty * cost_price

#     clamped_discount = max(
#         min_discount_percent,
#         min(discount_percent, max_discount_percent),
#     )

#     discount_amount = base * (clamped_discount / 100)
#     cgst_amount = base * (cgst_percent / 100)
#     sgst_amount = base * (sgst_percent / 100)

#     total = base + cgst_amount + sgst_amount - discount_amount
#     return total


# # async def create_batch(
# #     db: AsyncSession,
# #     batch: BatchCreate,
# # ) -> Batch:

# #     total_value = await calculate_total_value(
# #         batch.quantity_received,
# #         batch.cost_price,
# #         batch.gst_percent,
# #         batch.discount_percent,
# #         batch.cgst,
# #         batch.sgst,
# #     )

# #     db_obj = Batch(
# #         **batch.model_dump(),
# #         quantity_available=batch.quantity_received,
# #         total_value=total_value,
# #     )

# #     db.add(db_obj)
# #     await db.commit()
# #     await db.refresh(db_obj)


# #     await create_stock_ledger_entry(
# #         db=db,
# #         hospital_id=db_obj.hospital_id,
# #         branch_id=db_obj.branch_id,
# #         batch_id=db_obj.id,
# #         batch_type="MEDICINE_BATCH",
# #         transaction_type="RECEIPT",
# #         qty_in=batch.quantity_received,
# #         qty_out=0,
# #         balance_qty=batch.quantity_received,
# #         trans_value=total_value,
# #         remarks="Batch Received",
# #     )

# #     return db_obj


# # async def create_batch(db: AsyncSession, batch: BatchCreate) -> Batch:

# #     total_value = await calculate_total_value(
# #         batch.quantity_received,
# #         batch.cost_price,
# #         batch.gst_percent,
# #         batch.discount_percent,
# #         batch.cgst,
# #         batch.sgst,
# #     )

# #     db_obj = Batch(
# #         **batch.model_dump(),
# #         quantity_available=batch.quantity_received,
# #         total_value=total_value,
# #     )

# #     db.add(db_obj)
# #     await db.flush()  # get ID without committing

# #     await create_stock_ledger_entry(
# #         db=db,
# #         hospital_id=db_obj.hospital_id,
# #         branch_id=db_obj.branch_id,
# #         batch_id=db_obj.id,
# #         batch_type="MEDICINE_BATCH",
# #         transaction_type="RECEIPT",
# #         qty_in=batch.quantity_received,
# #         qty_out=0,
# #         balance_qty=batch.quantity_received,
# #         trans_value=total_value,
# #         remarks="Batch Received",
# #     )

# #     await db.commit()
# #     await db.refresh(db_obj)

# #     return db_obj

# async def create_batch(db: AsyncSession, batch_data: dict) -> Batch:
#     """
#     Create medicine batch and corresponding stock ledger entry
#     """

#     # Calculate total value
#     total_value = await calculate_total_value(
#         qty=batch_data["quantity_received"],
#         cost_price=batch_data["cost_price"],
#         gst_percent=batch_data.get("gst_percent", 0),
#         discount_percent=batch_data.get("discount_percent", 0),
#         cgst_percent=batch_data.get("cgst", 0),
#         sgst_percent=batch_data.get("sgst", 0),
#     )

#     # Create Batch object
#     db_obj = Batch(
#         **batch_data,
#         quantity_available=batch_data["quantity_received"],
#         total_value=total_value,
#     )

#     db.add(db_obj)
#     await db.flush()

#     # Create stock ledger entry
#     await create_stock_ledger_entry(
#     db=db,
#     hospital_id=batch_data["hospital_id"],   
#     branch_id=batch_data["branch_id"],       
#     batch_id=db_obj.id,
#     batch_type="MEDICINE_BATCH",
#     transaction_type="RECEIPT",
#     quantity_in=batch_data["quantity_received"],
#     quantity_out=0,
#     balance_qty=batch_data["quantity_received"],
#     transaction_value=total_value,
#     reference_id=db_obj.id,
#     remarks="Batch Received",
# )
#     await db.commit()
#     await db.refresh(db_obj)

#     return db_obj
#     await db.flush()  


# async def get_fefo_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     medicine_id: int,
#     required_qty: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch)
#         .where(
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#             Batch.medicine_id == medicine_id,
#             Batch.quantity_available >= required_qty,
#             Batch.expiry_date >= date.today(),
#         )
#         .order_by(asc(Batch.expiry_date))
#         .limit(1)
#     )

#     return result.scalar_one_or_none()

# async def update_batch_quantity(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
#     new_qty: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch).where(
#             Batch.id == batch_id,
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#     )

#     batch = result.scalar_one_or_none()

#     if batch:
#         batch.quantity_available = new_qty
#         await db.commit()
#         await db.refresh(batch)

#     return batch


# async def get_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch).where(
#             Batch.id == batch_id,
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#     )

#     return result.scalar_one_or_none()


# async def get_batches(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     skip: int = 0,
#     limit: int = 100,
#     medicine_id: Optional[int] = None,
#     search: Optional[str] = None,
# ) -> List[Batch]:

#     stmt = (
#         select(Batch)
#         .where(
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#         .options(selectinload(Batch.medicine))
#         .offset(skip)
#         .limit(limit)
#     )

#     if medicine_id:
#         stmt = stmt.where(Batch.medicine_id == medicine_id)

#     if search:
#         stmt = stmt.join(Medicine).where(
#             or_(
#                 Batch.batch_number.ilike(f"%{search}%"),
#                 Medicine.item_name.ilike(f"%{search}%"),
#                 Medicine.brand_name.ilike(f"%{search}%"),
#             )
#         )

#     result = await db.execute(stmt)
#     return result.scalars().all()


# async def update_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
#     batch_update: BatchUpdate,
# ) -> Batch | None:

#     batch = await get_batch(db, hospital_id, branch_id, batch_id)

#     if not batch:
#         return None

#     update_data = batch_update.model_dump(exclude_unset=True)

#     for field, value in update_data.items():
#         setattr(batch, field, value)

#     await db.commit()
#     await db.refresh(batch)

#     return batch


# async def delete_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
# ):

#     batch = await get_batch(db, hospital_id, branch_id, batch_id)

#     if batch:
#         await db.delete(batch)
#         await db.commit()





# from typing import List, Optional
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, asc, or_
# from sqlalchemy.orm import selectinload
# from datetime import date

# from app.models.entry_models import Batch, Medicine
# from app.schemas.entry_schemas import BatchCreate, BatchUpdate
# from app.crud.stock_ledger import create_stock_ledger_entry


# async def calculate_total_value(
#     qty: int,
#     cost_price: float,
#     gst_percent: float,
#     discount_percent: float,
#     cgst_percent: float,
#     sgst_percent: float,
#     min_discount_percent: float = 0.0,
#     max_discount_percent: float = 100.0,
# ) -> float:

#     base = qty * cost_price

#     clamped_discount = max(
#         min_discount_percent,
#         min(discount_percent, max_discount_percent),
#     )

#     discount_amount = base * (clamped_discount / 100)
#     cgst_amount = base * (cgst_percent / 100)
#     sgst_amount = base * (sgst_percent / 100)

#     total = base + cgst_amount + sgst_amount - discount_amount
#     return total


# async def create_batch(db: AsyncSession, batch_data: dict) -> Batch:
#     """
#     Create medicine batch and corresponding stock ledger entry.
#     batch_data must include hospital_id and branch_id.
#     """

#     hospital_id = batch_data.get("hospital_id")
#     branch_id = batch_data.get("branch_id")

#     # Safety check — should never be None if router injects them correctly
#     if not hospital_id or not branch_id:
#         raise ValueError(
#             f"hospital_id and branch_id must not be None. "
#             f"Got hospital_id={hospital_id}, branch_id={branch_id}. "
#             f"Check that the logged-in user has these fields set in the DB."
#         )

#     # Calculate total value
#     total_value = await calculate_total_value(
#         qty=batch_data["quantity_received"],
#         cost_price=batch_data["cost_price"],
#         gst_percent=batch_data.get("gst_percent", 0),
#         discount_percent=batch_data.get("discount_percent", 0),
#         cgst_percent=batch_data.get("cgst", 0),
#         sgst_percent=batch_data.get("sgst", 0),
#     )

#     # Create Batch ORM object
#     db_obj = Batch(
#         **batch_data,
#         quantity_available=batch_data["quantity_received"],
#         total_value=total_value,
#     )

#     db.add(db_obj)
#     await db.flush()  # get db_obj.id without committing yet

#     # Create stock ledger entry within same transaction
#     await create_stock_ledger_entry(
#         db=db,
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         batch_id=db_obj.id,
#         batch_type="MEDICINE_BATCH",
#         transaction_type="RECEIPT",
#         quantity_in=batch_data["quantity_received"],
#         quantity_out=0,
#         balance_qty=batch_data["quantity_received"],
#         transaction_value=total_value,
#         reference_id=db_obj.id,
#         remarks="Batch Received",
#     )

#     await db.commit()
#     await db.refresh(db_obj)

#     return db_obj


# async def get_fefo_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     medicine_id: int,
#     required_qty: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch)
#         .where(
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#             Batch.medicine_id == medicine_id,
#             Batch.quantity_available >= required_qty,
#             Batch.expiry_date >= date.today(),
#         )
#         .order_by(asc(Batch.expiry_date))
#         .limit(1)
#     )

#     return result.scalar_one_or_none()


# async def update_batch_quantity(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
#     new_qty: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch).where(
#             Batch.id == batch_id,
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#     )

#     batch = result.scalar_one_or_none()

#     if batch:
#         batch.quantity_available = new_qty
#         await db.commit()
#         await db.refresh(batch)

#     return batch


# async def get_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
# ) -> Batch | None:

#     result = await db.execute(
#         select(Batch).where(
#             Batch.id == batch_id,
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#     )

#     return result.scalar_one_or_none()


# async def get_batches(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     skip: int = 0,
#     limit: int = 100,
#     medicine_id: Optional[int] = None,
#     search: Optional[str] = None,
# ) -> List[Batch]:

#     stmt = (
#         select(Batch)
#         .where(
#             Batch.hospital_id == hospital_id,
#             Batch.branch_id == branch_id,
#         )
#         .options(selectinload(Batch.medicine))
#         .offset(skip)
#         .limit(limit)
#     )

#     if medicine_id:
#         stmt = stmt.where(Batch.medicine_id == medicine_id)

#     if search:
#         stmt = stmt.join(Medicine).where(
#             or_(
#                 Batch.batch_number.ilike(f"%{search}%"),
#                 Medicine.item_name.ilike(f"%{search}%"),
#                 Medicine.brand_name.ilike(f"%{search}%"),
#             )
#         )

#     result = await db.execute(stmt)
#     return result.scalars().all()


# async def update_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
#     batch_update: BatchUpdate,
# ) -> Batch | None:

#     batch = await get_batch(db, hospital_id, branch_id, batch_id)

#     if not batch:
#         return None

#     update_data = batch_update.model_dump(exclude_unset=True)

#     for field, value in update_data.items():
#         setattr(batch, field, value)

#     await db.commit()
#     await db.refresh(batch)

#     return batch


# async def delete_batch(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
# ):

#     batch = await get_batch(db, hospital_id, branch_id, batch_id)

#     if batch:
#         await db.delete(batch)
#         await db.commit()

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, or_
from sqlalchemy.orm import selectinload
from datetime import date

from app.models.entry_models import Batch, Medicine
from app.schemas.entry_schemas import BatchCreate, BatchUpdate
from app.services.stock_ledger import create_stock_ledger_entry


async def calculate_total_value(
    qty: int,
    cost_price: float,
    gst_percent: float,
    discount_percent: float,
    cgst_percent: float,
    sgst_percent: float,
    min_discount_percent: float = 0.0,
    max_discount_percent: float = 100.0,
) -> float:

    base = qty * cost_price

    clamped_discount = max(
        min_discount_percent,
        min(discount_percent, max_discount_percent),
    )

    discount_amount = base * (clamped_discount / 100)
    cgst_amount = base * (cgst_percent / 100)
    sgst_amount = base * (sgst_percent / 100)

    total = base + cgst_amount + sgst_amount - discount_amount
    return total


async def create_batch(db: AsyncSession, batch_data: dict) -> Batch:
    """
    Create medicine batch and corresponding stock ledger entry.
    batch_data must in clude hospital_id and branch_id.
    """

    hospital_id = batch_data.get("hospital_id")
    branch_id = batch_data.get("branch_id")

    if not hospital_id or not branch_id:
        raise ValueError(
            f"hospital_id and branch_id must not be None. "
            f"Got hospital_id={hospital_id}, branch_id={branch_id}. "
            f"Check that the logged-in user has these fields set in the DB."
        )

    total_value = await calculate_total_value(
        qty=batch_data["quantity_received"],
        cost_price=batch_data["cost_price"],
        gst_percent=batch_data.get("gst_percent", 0),
        discount_percent=batch_data.get("discount_percent", 0),
        cgst_percent=batch_data.get("cgst", 0),
        sgst_percent=batch_data.get("sgst", 0),
    )

    db_obj = Batch(
        **batch_data,
        quantity_available=batch_data["quantity_received"],
        total_value=total_value,
    )

    db.add(db_obj)
    await db.flush()  # get db_obj.id without committing yet

    await create_stock_ledger_entry(
        db=db,
        hospital_id=hospital_id,
        branch_id=branch_id,
        batch_id=db_obj.id,
        batch_type="MEDICINE_BATCH",
        transaction_type="RECEIPT",
        quantity_in=batch_data["quantity_received"],
        quantity_out=0,
        balance_qty=batch_data["quantity_received"],
        transaction_value=total_value,
        reference_id=db_obj.id,
        remarks="Batch Received",
    )

    await db.commit()
    await db.refresh(db_obj)

    return db_obj


async def get_fefo_batch(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    medicine_id: int,
    required_qty: int,
) -> Batch | None:

    result = await db.execute(
        select(Batch)
        .where(
            Batch.hospital_id == hospital_id,
            Batch.branch_id == branch_id,
            Batch.medicine_id == medicine_id,
            Batch.quantity_available >= required_qty,
            Batch.expiry_date >= date.today(),
        )
        .order_by(asc(Batch.expiry_date))
        .limit(1)
    )

    return result.scalar_one_or_none()


async def update_batch_quantity(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    batch_id: int,
    new_qty: int,
) -> Batch | None:

    result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.hospital_id == hospital_id,
            Batch.branch_id == branch_id,
        )
    )

    batch = result.scalar_one_or_none()

    if batch:
        batch.quantity_available = new_qty
        await db.commit()
        await db.refresh(batch)

    return batch


async def get_batch(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    batch_id: int,
) -> Batch | None:

    result = await db.execute(
        select(Batch).where(
            Batch.id == batch_id,
            Batch.hospital_id == hospital_id,
            Batch.branch_id == branch_id,
        )
    )

    return result.scalar_one_or_none()


async def get_batches(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    skip: int = 0,
    limit: int = 100,
    medicine_id: Optional[int] = None,
    search: Optional[str] = None,
) -> List[Batch]:

    stmt = (
        select(Batch)
        .where(
            Batch.hospital_id == hospital_id,
            Batch.branch_id == branch_id,
        )
        .options(selectinload(Batch.medicine))
        .offset(skip)
        .limit(limit)
    )

    if medicine_id:
        stmt = stmt.where(Batch.medicine_id == medicine_id)

    if search:
        stmt = stmt.join(Medicine).where(
            or_(
                Batch.batch_number.ilike(f"%{search}%"),
                Medicine.item_name.ilike(f"%{search}%"),
                Medicine.brand_name.ilike(f"%{search}%"),
            )
        )

    result = await db.execute(stmt)
    return result.scalars().all()


async def update_batch(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    batch_id: int,
    batch_update: BatchUpdate,
) -> Batch | None:

    batch = await get_batch(db, hospital_id, branch_id, batch_id)

    if not batch:
        return None

    update_data = batch_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(batch, field, value)

    await db.commit()
    await db.refresh(batch)

    return batch


async def delete_batch(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    batch_id: int,
):

    batch = await get_batch(db, hospital_id, branch_id, batch_id)

    if batch:
        await db.delete(batch)
        await db.commit()