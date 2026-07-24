# from datetime import datetime, timedelta
# from typing import List, Optional, Union
# import uuid
# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from sqlalchemy.orm import Session
# load_dotenv()
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from argon2 import PasswordHasher
# from argon2.exceptions import VerifyMismatchError
# from app.core.security import get_db
#
# from fastapi import Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
#
# # from app.models.role_ import  BillingSummary
# from app.models.discounts import DiscountAudit
# from app.models.auth import User
# from app.models.role_based import BillingSummary
#
#
#
# # Read from environment (.env loaded in main.py)
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM", "HS256")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
#
# UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
# UPLOAD_DIR.mkdir(exist_ok=True)
#
# # Argon2 password hasher
# ph = PasswordHasher()
#
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
#
# # Shift times directly from .env as STRINGS (no parsing)
# PREDEFINED_SHIFTS = {
#     "A": {
#         "start_time": os.getenv("SHIFT_A_START", "06:00"),
#         "end_time": os.getenv("SHIFT_A_END", "14:00")
#     },
#     "B": {
#         "start_time": os.getenv("SHIFT_B_START", "14:00"),
#         "end_time": os.getenv("SHIFT_B_END", "22:00")
#     },
#     "C": {
#         "start_time": os.getenv("SHIFT_C_START", "22:00"),
#         "end_time": os.getenv("SHIFT_C_END", "06:00")
#     },
#     "D": {
#         "start_time": os.getenv("SHIFT_D_START", "10:00"),
#         "end_time": os.getenv("SHIFT_D_END", "19:00")
#     },
# }
#
#
# def verify_password(plain: str, hashed: str) -> bool:
#     try:
#         return ph.verify(hashed, plain)
#     except VerifyMismatchError:
#         return False
#
#
# def get_password_hash(password: str) -> str:
#     return ph.hash(password)
#
#
# def create_session_id() -> str:
#     return uuid.uuid4().hex
#
#
# def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
#     if not SECRET_KEY:
#         raise RuntimeError("SECRET_KEY is not set in environment")
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#
#
# async def get_current_user(
#     token: str = Depends(oauth2_scheme),
#     db: AsyncSession = Depends(get_db),
# ) -> User:
#     if not SECRET_KEY:
#         raise RuntimeError("SECRET_KEY is not set in environment")
#     cred_exc = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: Optional[str] = payload.get("sub")
#         session_id: Optional[str] = payload.get("sid")
#
#
#
#         if username is None or session_id is None:
#             raise cred_exc
#     except JWTError:
#         raise cred_exc
#
#     result = await db.execute(select(User).where(User.username == username))
#     user = result.scalar_one_or_none()
#
#
#     if not user or not user.is_active:
#         raise cred_exc
#     if user.active_session_id != session_id:
#         raise cred_exc
#
#     return user
#
#
# def role_required(allowed_roles):
#     if isinstance(allowed_roles, str):
#         roles = [allowed_roles.upper()]
#     else:
#         roles = [r.upper() for r in allowed_roles]
#
#     async def _checker(current_user: User = Depends(get_current_user)) -> User:
#         if current_user.role.upper() not in roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Insufficient role",
#             )
#         return current_user
#     return _checker
#
#
# # Limits for discount abuse
# DISCOUNT_COUNT_LIMIT = 5
# DISCOUNT_VALUE_LIMIT = 1000  # ₹1000 per day
#
# ALLOWED_ROLES = {"pharmacist", "manager", "accounting"}
#
#
# # -------------------- USER DEPENDENCY --------------------
# # async def get_current_user() -> User:
#
# #     return User(id=1,  username="dummy", role="pharmacist")
#
#
# # -------------------- ROLE-BASED ACCESS --------------------
# # def role_required(allowed_roles: list):
#
# #     async def checker(current_user: User = Depends(get_current_user)):
# #         if current_user.role not in allowed_roles:
# #             raise HTTPException(
# #                 status_code=status.HTTP_403_FORBIDDEN,
# #                 detail="Permission denied"
# #             )
# #         return current_user
# #     return checker
#
#
# # -------------------- PAYROLL CALCULATION --------------------
# async def calculate_payroll_from_shifts(
#     *,
#     base_salary: float,
#     night_shift_count: int,
#     overtime_hours: int,
#     total_sales: float
# ) -> dict:
#     shift_allowance = night_shift_count * 500
#     night_allowance = night_shift_count * 300
#     overtime_pay = overtime_hours * 200
#     incentive = total_sales * 0.02
#
#     total_salary = base_salary + shift_allowance + night_allowance + overtime_pay + incentive
#
#     return {
#         "shift_allowance": shift_allowance,
#         "night_allowance": night_allowance,
#         "overtime_pay": overtime_pay,
#         "incentive": incentive,
#         "total_salary": total_salary
#     }
#
#
# # -------------------- DISCOUNT ABUSE DETECTION --------------------
# # async def detect_discount_abuse(
# #     pharmacist_id: int,
# #     db: AsyncSession
# # ) -> tuple[bool, str | None]:
# #     result = await db.execute(
# #         select(DiscountAudit)
# #         .where(DiscountAudit.pharmacist_id == pharmacist_id)
# #     )
# #     discounts = result.scalars().all()
# #
# #     if len(discounts) >= DISCOUNT_COUNT_LIMIT:
# #         return True, "Too many discounts applied by pharmacist"
# #
# #     total_discount_value = sum(d.discount_value for d in discounts)
# #     if total_discount_value >= DISCOUNT_VALUE_LIMIT:
# #         return True, "High total discount value detected"
# #
# #     return False, None
#
# async def detect_discount_abuse(
#     pharmacist_id: int,
#     db: AsyncSession
# ) -> tuple[bool, str | None]:
#     result = await db.execute(
#         select(DiscountAudit).where(
#             DiscountAudit.pharmacist_id == pharmacist_id
#         )
#     )
#
#     discounts = result.scalars().all()
#
#     if len(discounts) >= DISCOUNT_COUNT_LIMIT:
#         return True, "Too many discounts applied by pharmacist"
#
#     total_discount_value = sum(d.discount_value for d in discounts)
#
#     if total_discount_value >= DISCOUNT_VALUE_LIMIT:
#         return True, "High total discount value detected"
#
#     return False, None
#
#
# # -------------------- SHIFT COLLECTION RECONCILIATION --------------------
# async def reconcile_shift_collection(
#     shift_id: int,
#     expected_total: float,
#     db: AsyncSession
# ) -> dict:
#     result = await db.execute(
#         select(BillingSummary)
#         .where(BillingSummary.shift_id == shift_id)
#     )
#     billing = result.scalar_one_or_none()
#
#     if not billing:
#         return {
#             "status": "FAILED",
#             "reason": "Billing data not found"
#         }
#
#     actual_total = billing.cash_amount + billing.upi_amount + billing.card_amount
#
#     if actual_total != expected_total:
#         return {
#             "status": "MISMATCH",
#             "expected": expected_total,
#             "actual": actual_total
#         }
#
#     return {
#         "status": "MATCHED",
#         "total": actual_total
#     }
