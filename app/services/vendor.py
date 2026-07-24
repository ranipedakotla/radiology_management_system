# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from app.models.vendor import Vendor

# async def get_vendors(db: AsyncSession):
#     result = await db.execute(select(Vendor))
#     return result.scalars().all()

# async def get_vendor(db: AsyncSession, vendor_id: int):
#     result = await db.execute(select(Vendor).filter(Vendor.id == vendor_id))
#     return result.scalar_one_or_none()

# async def create_vendor(db: AsyncSession, vendor):
#     db.add(vendor)
#     await db.commit()
#     await db.refresh(vendor)
#     return vendor

# async def update_vendor(db: AsyncSession, vendor_id: int, vendor_data: dict):
#     vendor = await get_vendor(db, vendor_id)
#     if vendor:
#         for key, value in vendor_data.items():
#             setattr(vendor, key, value)
#         await db.commit()
#         await db.refresh(vendor)
#     return vendor

# async def delete_vendor(db: AsyncSession, vendor_id: int):
#     vendor = await get_vendor(db, vendor_id)
#     if vendor:
#         await db.delete(vendor)
#         await db.commit()
#     return vendor

from sqlalchemy import select, func ,case
from app.models.vendor import Vendor, VendorTransaction
from sqlalchemy.ext.asyncio import AsyncSession

# async def calculate_vendor_payable(db, vendor_id, hospital_id, branch_id):
#     result = await db.execute(
#         select(
#             func.coalesce(
#                 func.sum(
#                     func.case(
#                         (VendorTransaction.type == "credit", VendorTransaction.amount),
#                         (VendorTransaction.type == "debit", -VendorTransaction.amount),
#                         else_=0
#                     )
#                 ), 0
#             )
#         ).where(
#             VendorTransaction.vendor_id == vendor_id,
#             VendorTransaction.hospital_id == hospital_id,
#             VendorTransaction.branch_id == branch_id
#         )
#     )
#     return result.scalar()


async def calculate_vendor_payable(
    db,
    vendor_id: int,
    hospital_id: int,
    branch_id: int
):
    result = await db.execute(
        select(
            func.sum(
                case(
                    (VendorTransaction.type == "credit", VendorTransaction.amount),
                    (VendorTransaction.type == "debit", -VendorTransaction.amount),
                    else_=0
                )
            )
        ).where(
            VendorTransaction.vendor_id == vendor_id,
            VendorTransaction.hospital_id == hospital_id,
            VendorTransaction.branch_id == branch_id
        )
    )

    total = result.scalar()
    return total or 0

async def get_vendor_by_id(
    db: AsyncSession,
    vendor_id: int,
    hospital_id: int,
    branch_id: int
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id
        )
    )
    return result.scalar_one_or_none()