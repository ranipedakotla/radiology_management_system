import os
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import (create_async_engine,AsyncSession,async_sessionmaker)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from app.db.session import SessionLocal, AsyncSessionLocal
from app.models.auth import User, Role
from app.core.settings import settings
from app.models.discounts import DiscountAudit
from app.models.role_based import BillingSummary

# pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

oauth2_scheme = HTTPBearer()



UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# Shift times directly from .env as STRINGS (no parsing)
PREDEFINED_SHIFTS = {
    "A": {
        "start_time": os.getenv("SHIFT_A_START", "06:00"),
        "end_time": os.getenv("SHIFT_A_END", "14:00")
    },
    "B": {
        "start_time": os.getenv("SHIFT_B_START", "14:00"),
        "end_time": os.getenv("SHIFT_B_END", "22:00")
    },
    "C": {
        "start_time": os.getenv("SHIFT_C_START", "22:00"),
        "end_time": os.getenv("SHIFT_C_END", "06:00")
    },
    "D": {
        "start_time": os.getenv("SHIFT_D_START", "10:00"),
        "end_time": os.getenv("SHIFT_D_END", "19:00")
    },
}

# --- DB dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def async_get_db():
    async with AsyncSessionLocal() as db:
        yield db

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     except:
#         db.close()

# --- password utils ---
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

# --- JWT helpers ---
def _encode(sub: str, claims: dict, minutes: int):
    now = datetime.utcnow()
    payload = {"sub": sub, "iat": now, "exp": now + timedelta(minutes=minutes), **claims}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token_for_user(user, tenant=None, expires_delta=None):
    roles = [r.name for r in getattr(user, "roles", [])]

    print("USER ID:", user.id)
    print("USER ROLE:", user.role)

    claims = {
        "sub": str(user.id),
        "email": user.email,
        # "roles": roles,
        "roles": [user.role.lower()],
    }
    print("TOKEN GENERATED")
    # multi-branch context
    if tenant:
        claims["hid"] = getattr(tenant, "hospital_id", None)
        claims["bid"] = getattr(tenant, "branch_id", None)
    else:
        claims["hid"] = getattr(user, "hospital_id", None)
        claims["bid"] = getattr(user, "current_branch_id", None)

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    claims["exp"] = expire

    # NOTE: use JWT_SECRET as defined in your settings.py
    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token




#
# def get_current_user(credentials:HTTPAuthorizationCredentials= Depends(oauth2_scheme)) -> User:
#     token = credentials.credentials
#     print("token", token)
#
#     if not token or token.count(".") != 2:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or missing authentication token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     try:
#         payload = jwt.decode(
#             token,
#             settings.JWT_SECRET,
#             algorithms=[settings.JWT_ALGORITHM],
#         )
#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     print("payload", payload)
#
#     user_id = int(payload["sub"])
#
#     with SessionLocal() as db:
#         stmt = (
#             select(User)
#             .where(User.id == user_id)
#             .options(
#                 selectinload(User.roles).selectinload(Role.permissions),
#                 joinedload(User.hospital),
#                 joinedload(User.current_branch),
#             )
#         )
#         user = db.execute(stmt).scalar_one_or_none()
#
#         if not user or not user.is_active:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid or inactive user",
#             )
#
#         # attach tenant context from token to the user object (handy for request scope)
#         user.hospital_id = payload.get("hospital_id") or user.hospital_id
#         user.current_branch_id = payload.get("branch_id") or user.current_branch_id
#
#         return user


#
# async def get_current_user(credentials:HTTPAuthorizationCredentials= Depends(oauth2_scheme)) -> User:
#     token = credentials.credentials
#     print("token", token)
#
#     if not token or token.count(".") != 2:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or missing authentication token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     try:
#         payload = jwt.decode(
#             token,
#             settings.JWT_SECRET,
#             algorithms=[settings.JWT_ALGORITHM],
#         )
#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     print("payload", payload)
#
#     user_id = int(payload["sub"])
#
#     # async with SessionLocal() as db:
#     with SessionLocal() as db:
#
#         stmt = (
#             select(User)
#             .where(User.id == user_id)
#             .options(
#                 selectinload(User.roles).selectinload(Role.permissions),
#                  joinedload(User.hospital),
#                 joinedload(User.current_branch),
#             )
#         )
#
#         # result = await db.execute(stmt)
#         result = db.execute(stmt)
#         user = result.scalar_one_or_none()
#
#         if not user or not user.is_active:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid or inactive user",
#             )
#
#         # attach tenant context from token to the user object (handy for request scope)
#         user.hospital_id = payload.get("hospital_id") or user.hospital_id
#         user.current_branch_id = payload.get("branch_id") or user.current_branch_id
#
#         return user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> User:

    token = credentials.credentials

    if not token or token.count(".") != 2:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(payload["sub"])

    async with AsyncSessionLocal() as db:

        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles).selectinload(Role.permissions),
                joinedload(User.hospital),
                joinedload(User.current_branch),
            )
        )

        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive user",
            )

        # Read the same keys you stored in the token
        user.hospital_id = payload.get("hospital_id") or user.hospital_id
        user.current_branch_id = payload.get("branch_id") or user.current_branch_id

        return user

# --- guards ---
# def require_roles(*allowed: str):
#     def wrapper(user: User = Depends(get_current_user)):
#         role_names = {r.name for r in user.roles}
#         if role_names.isdisjoint(set(allowed)):
#             raise HTTPException(status_code=403, detail="Forbidden")
#         return user
#     return wrapper
#
# def require_permissions(*perms: str):
#     def wrapper(user: User = Depends(get_current_user)):
#         user_perms = {p.code for r in user.roles for p in r.permissions}
#         if not set(perms).issubset(user_perms):
#             raise HTTPException(status_code=403, detail="Missing permissions")
#         return user
#     return wrapper
# def require_roles(*allowed):
#     normalized = set()
#
#     for item in allowed:
#         if isinstance(item, (list, tuple, set)):
#             normalized.update(item)
#         else:
#             normalized.add(item)
#
#     def wrapper(user: User = Depends(get_current_user)):
#         role_names = {r.name for r in user.roles}
#
#         if role_names.isdisjoint(normalized):
#             raise HTTPException(
#                 status_code=403,
#                 detail="Forbidden"
#             )
#
#         return user
#
#     return wrapper
def require_roles(*allowed):
    normalized = set()

    for item in allowed:
        if isinstance(item, (list, tuple, set)):
            normalized.update(r.lower() for r in item)
        else:
            normalized.add(item.lower())

    def wrapper(user: User = Depends(get_current_user)):
        role_names = {user.role.lower()}

        print("User:", user.username)
        print("Roles:", role_names)
        print("Allowed:", normalized)

        if role_names.isdisjoint(normalized):
            raise HTTPException(
                status_code=403,
                detail="Forbidden"
            )

        return user

    return wrapper


# Limits for discount abuse
DISCOUNT_COUNT_LIMIT = 5
DISCOUNT_VALUE_LIMIT = 1000  # ₹1000 per day

ALLOWED_ROLES = {"pharmacist", "manager", "accounting"}


# -------------------- USER DEPENDENCY --------------------
# async def get_current_user() -> User:

#     return User(id=1,  username="dummy", role="pharmacist")


# -------------------- ROLE-BASED ACCESS --------------------
# def role_required(allowed_roles: list):

#     async def checker(current_user: User = Depends(get_current_user)):
#         if current_user.role not in allowed_roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Permission denied"
#             )
#         return current_user
#     return checker


# -------------------- PAYROLL CALCULATION --------------------
async def calculate_payroll_from_shifts(
    *,
    base_salary: float,
    night_shift_count: int,
    overtime_hours: int,
    total_sales: float
) -> dict:
    shift_allowance = night_shift_count * 500
    night_allowance = night_shift_count * 300
    overtime_pay = overtime_hours * 200
    incentive = total_sales * 0.02

    total_salary = base_salary + shift_allowance + night_allowance + overtime_pay + incentive

    return {
        "shift_allowance": shift_allowance,
        "night_allowance": night_allowance,
        "overtime_pay": overtime_pay,
        "incentive": incentive,
        "total_salary": total_salary
    }


# -------------------- DISCOUNT ABUSE DETECTION --------------------
# async def detect_discount_abuse(
#     pharmacist_id: int,
#     db: AsyncSession
# ) -> tuple[bool, str | None]:
#     result = await db.execute(
#         select(DiscountAudit)
#         .where(DiscountAudit.pharmacist_id == pharmacist_id)
#     )
#     discounts = result.scalars().all()
#
#     if len(discounts) >= DISCOUNT_COUNT_LIMIT:
#         return True, "Too many discounts applied by pharmacist"
#
#     total_discount_value = sum(d.discount_value for d in discounts)
#     if total_discount_value >= DISCOUNT_VALUE_LIMIT:
#         return True, "High total discount value detected"
#
#     return False, None

async def detect_discount_abuse(
    pharmacist_id: int,
    db: AsyncSession
) -> tuple[bool, str | None]:
    result = await db.execute(
        select(DiscountAudit).where(
            DiscountAudit.pharmacist_id == pharmacist_id
        )
    )

    discounts = result.scalars().all()

    if len(discounts) >= DISCOUNT_COUNT_LIMIT:
        return True, "Too many discounts applied by pharmacist"

    total_discount_value = sum(d.discount_value for d in discounts)

    if total_discount_value >= DISCOUNT_VALUE_LIMIT:
        return True, "High total discount value detected"

    return False, None


# -------------------- SHIFT COLLECTION RECONCILIATION --------------------
async def reconcile_shift_collection(
    shift_id: int,
    expected_total: float,
    db: AsyncSession
) -> dict:
    result = await db.execute(
        select(BillingSummary)
        .where(BillingSummary.shift_id == shift_id)
    )
    billing = result.scalar_one_or_none()

    if not billing:
        return {
            "status": "FAILED",
            "reason": "Billing data not found"
        }

    actual_total = billing.cash_amount + billing.upi_amount + billing.card_amount

    if actual_total != expected_total:
        return {
            "status": "MISMATCH",
            "expected": expected_total,
            "actual": actual_total
        }

    return {
        "status": "MATCHED",
        "total": actual_total
    }

#pathology

# from datetime import datetime, timedelta, timezone
# from typing import Iterable
#
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import jwt
# from passlib.context import CryptContext
# from sqlalchemy.orm import Session
#
# from app.core.config import settings
# from app.db.session import get_db
# from app.models.user import User
#
# pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")
#
#
# def hash_pwd(p: str) -> str:
#     return pwd_ctx.hash(p)
#
#
# def verify_pwd(p: str, hashed: str) -> bool:
#     return pwd_ctx.verify(p, hashed)
#
#
# def create_access_token(sub: str, roles: list[str]) -> str:
#     now = datetime.now(tz=timezone.utc)
#     exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     payload = {"sub": sub, "roles": roles, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
#     return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGO)
#
#
# def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2)) -> User:
#     try:
#         payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGO])
#         sub = payload.get("sub")
#         if not sub:
#             raise ValueError("No sub")
#     except Exception:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
#     user = db.query(User).filter(User.email == sub).one_or_none()
#     if not user or not user.is_active:
#         raise HTTPException(status_code=401, detail="Inactive user")
#     return user
#
#
# def require_roles(allowed: Iterable[str]):
#     allowed = set(allowed)
#
#     def dep(user: User = Depends(get_current_user)):
#         names = {r.name for r in user.roles}
#         if not (allowed & names):
#             raise HTTPException(status_code=403, detail="Insufficient role")
#         return user
#
#     return dep
