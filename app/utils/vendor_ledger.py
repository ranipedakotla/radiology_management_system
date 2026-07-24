from sqlalchemy import select, func, case
from app.models.vendor import VendorTransaction

async def calculate_vendor_payable(db, vendor_id, hospital_id, branch_id):
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (VendorTransaction.type == "credit", VendorTransaction.amount),
                        (VendorTransaction.type == "debit", -VendorTransaction.amount),
                        else_=0
                    )
                ),
                0
            )
        ).where(
            VendorTransaction.vendor_id == vendor_id,
            VendorTransaction.hospital_id == hospital_id,
            VendorTransaction.branch_id == branch_id
        )
    )
    return result.scalar()