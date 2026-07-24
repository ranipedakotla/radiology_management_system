# from app.models.quotations import Quotation
# #
# # from app.schemas import Vendor
# from app.models.vendor import Vendor
#
#
# # select(vendor)
#
# async def select_best_quotation(quotations: list[Quotation]):
#     sorted_q = sorted(
#         quotations,
#         key=lambda q: (q.price, -q.vendor_score)
#     )
#     return sorted_q[0] if sorted_q else None
#
# async def calculate_item_totals(
#     price: float,
#     quantity: int,
#     cgst: float,
#     sgst: float,
#     discount: float
# ):
#     base_total = price * quantity
#     gst_amount = (base_total * (cgst + sgst)) / 100
#     total_price = base_total + gst_amount
#     final_price = total_price - discount
#
#     return total_price, final_price
#
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# # from app.models import vendor
#
# async def get_vendor_by_id(db: AsyncSession, vendor_id: int):
#     result = await db.execute(select(Vendor).where(Vendor.id == vendor_id))
#     return result.scalar_one_or_none()
#
# async def get_vendor_by_gst(db: AsyncSession, gst_no: str):
#     result = await db.execute(select(Vendor).where(Vendor.gst_no == gst_no))
#     return result.scalar_one_or_none()

from typing import List, Optional


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.vendor import Vendor
from app.models.quotations import Quotation


#  SYNC: Pure business logic
# def select_best_quotation(quotations: List[Quotation]) -> Optional[Quotation]:
#     if not quotations:
#         return None
#
#     return sorted(
#         quotations,
#         key=lambda q: ( -q.vendor_score)
#     )[0]

# def select_best_quotation(
#     quotations: List[Quotation]
# ) -> Optional[Quotation]:
#
#     if not quotations:
#         return None
#
#     return min(
#         quotations,
#         key=lambda q: q.net_amount
#     )

def select_best_quotation(
    quotations: List[Quotation]
) -> Optional[Quotation]:

    if not quotations:
        return None

    return min(
        quotations,
        key=lambda q: (
            q.net_amount,
            -(q.vendor.delivery_timeliness or 0),
            -(q.vendor.price_consistency or 0)
        )
    )

#  SYNC: Pure calculation (THIS FIXES YOUR ERROR)
def calculate_item_totals(
    price: float,
    quantity: int,
    cgst: float,
    sgst: float,
    discount: float,
):
    base_total = price * quantity
    gst_amount = (base_total * (cgst + sgst)) / 100
    total_price = base_total + gst_amount
    final_price = total_price - discount

    return total_price, final_price

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
            Vendor.branch_id == branch_id,
            Vendor.is_active == True
        )
    )
    return result.scalar_one_or_none()


# ---------------- GET VENDOR BY GST ----------------

async def get_vendor_by_gst(
    db: AsyncSession,
    gst_no: str,
    hospital_id: int,
    branch_id: int
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.gst_no == gst_no,
            Vendor.hospital_id == hospital_id,
            Vendor.branch_id == branch_id,
            Vendor.is_active == True
        )
    )
    return result.scalar_one_or_none()

# services/vendor_service.py

def calculate_rating(vendor):
    score = (
        vendor.delivery_timeliness +
        vendor.medicine_quality +
        vendor.price_consistency +
        vendor.payment_history -
        vendor.expiry_risk
    ) / 5

    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Blacklisted"




