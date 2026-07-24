import enum
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import Ledger


LedgerType = ["CREDIT", "DEBIT"]

def validate_ledger_type(value: str):
    if value not in LedgerType:
        raise ValueError("Invalid ledger type")
        
    
async def post_ledger(
    db: AsyncSession,
    ledger_type,
    hospital_id,
    branch_id,
    reference_id,
    amount,
):
    entry = Ledger(
        ledger_type=ledger_type,
        hospital_id=hospital_id,
        branch_id=branch_id,
        reference_id=reference_id,
        amount=amount,
    )
    db.add(entry)
    await db.commit()
