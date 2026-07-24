# # from sqlalchemy.ext.asyncio import AsyncSession
# # from sqlalchemy import select
# # from app.models.entry_models import StockLedger


# # async def create_stock_ledger_entry(
# #     db: AsyncSession,
# #     batch_id: int,
# #     batch_type: str,
# #     transaction_type: str,
# #     quantity_in: int,
# #     quantity_out: int,
# #     balance_qty: int,
# #     transaction_value: float,
# #     reference_id: int, 
# #     remarks: str
# # ) -> StockLedger:

# #     db_obj = StockLedger(
# #         batch_type=batch_type,
# #         batch_id=batch_id,
# #         transaction_type=transaction_type,
# #         quantity_in=quantity_in,
# #         quantity_out=quantity_out,
# #         balance_qty=balance_qty,
# #         transaction_value=transaction_value,
# #         reference_type="PHARMACY_ISSUE",
# #         reference_id=reference_id,
# #         remarks=remarks
# #     )

# #     db.add(db_obj)
# #     await db.commit()
# #     await db.refresh(db_obj)

# #     return db_obj

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from app.models.entry_models import StockLedger

# async def create_stock_ledger_entry(
#     db: AsyncSession,
#     hospital_id: int,
#     branch_id: int,
#     batch_id: int,
#     batch_type: str,
#     transaction_type: str,
#     quantity_in: int,
#     quantity_out: int,
#     balance_qty: int,
#     transaction_value: float,
#     reference_id: int,
#     remarks: str
# ) -> StockLedger:

#     db_obj = StockLedger(
#         hospital_id=hospital_id,
#         branch_id=branch_id,
#         batch_type=batch_type,
#         batch_id=batch_id,
#         transaction_type=transaction_type,
#         quantity_in=quantity_in,
#         quantity_out=quantity_out,
#         balance_qty=balance_qty,
#         transaction_value=transaction_value,
#         reference_type="PHARMACY_ISSUE",
#         reference_id=reference_id,
#         remarks=remarks
#     )

#     db.add(db_obj)
#     await db.flush()

#     return db_obj

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entry_models import StockLedger


async def create_stock_ledger_entry(
    db: AsyncSession,
    hospital_id: int,
    branch_id: int,
    batch_id: int,
    batch_type: str,
    transaction_type: str,
    quantity_in: int,
    quantity_out: int,
    balance_qty: int,
    transaction_value: float,
    reference_id: int,
    remarks: str,
) -> StockLedger:

    db_obj = StockLedger(
        hospital_id=hospital_id,
        branch_id=branch_id,
        batch_type=batch_type,
        batch_id=batch_id,
        transaction_type=transaction_type,
        quantity_in=quantity_in,
        quantity_out=quantity_out,
        balance_qty=balance_qty,
        transaction_value=transaction_value,
        reference_type="PHARMACY_ISSUE",
        reference_id=reference_id,
        remarks=remarks,
    )

    db.add(db_obj)
    await db.flush()  # flush within the same transaction — commit handled by caller

    return db_obj