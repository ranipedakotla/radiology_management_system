from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.discounts import (
    Membership, PromoCode, SeasonalDiscount
)

async def apply_membership_discount(phone: str, amount: float, db: AsyncSession):
    today = date.today()

    result = await db.execute(
        select(Membership).where(
            Membership.phone_number == phone,
            Membership.is_active == True,
            Membership.valid_from <= today,
            Membership.valid_to >= today
        )
    )
    member = result.scalars().first()
    if not member:
        return amount, 0, "No active membership found"

    discount = amount * (member.discount_percent / 100)
    return amount - discount, discount, "Membership Discount Applied"


async def apply_seasonal_discount(amount: float, db: AsyncSession):
    today = date.today()

    result = await db.execute(
        select(SeasonalDiscount).where(
            SeasonalDiscount.valid_from <= today,
            SeasonalDiscount.valid_to >= today,
            SeasonalDiscount.is_active == True
        )
    )
    seasonal = result.scalars().first()
    if not seasonal:
        return amount, 0

    discount = amount * (seasonal.discount_percent / 100)
    return amount - discount, discount


async def apply_promo_code(code: str, amount: float, db: AsyncSession):
    today = date.today()

    result = await db.execute(
        select(PromoCode).where(
            PromoCode.code == code,
            PromoCode.is_active == True,
            PromoCode.valid_from <= today,
            PromoCode.valid_to >= today,
            PromoCode.min_bill_value <= amount
        )
    )
    promo = result.scalars().first()
    if not promo:
        return amount, 0, "Invalid or expired promo code"

    if promo.discount_percent:
        discount = amount * (promo.discount_percent / 100)
    else:
        discount = promo.flat_amount

    return amount - discount, discount, "Promo Code Applied"
