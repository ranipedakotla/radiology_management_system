
from fastapi import HTTPException
from sqlalchemy import select

from app.db.session import SessionLocal, AsyncSessionLocal
from app.core.security import verify_password, create_access_token_for_user
from app.models.auth import User,Role

from app.utils.tenant import Tenant
from sqlalchemy.orm import selectinload

# class AuthService:
#     def login(self, email: str, password: str, tenant: Tenant | None = None) -> str:
#
#         with SessionLocal() as db:
#             user: User | None = db.query(User).filter(User.email == email).first()
#
#             print("User:", user.email if user else None)
#             print("Password entered:", password)
#
#             if user:
#                 print("Stored hash:", user.password_hash)
#                 print("Password match:", verify_password(password, user.password_hash))
#
#             if not user or not verify_password(password, user.password_hash):
#                 raise HTTPException(status_code=401, detail="Invalid credentials")
#
#             return create_access_token_for_user(user, tenant=tenant)



class AuthService:
    async def login(self, email: str, password: str, tenant: Tenant | None = None) -> str:

        async with AsyncSessionLocal() as db:

            result = await db.execute(
                select(User)
                .options(
                    selectinload(User.roles)
                )
                .where(User.email == email)
            )

            user: User | None = result.scalar_one_or_none()

            print("User:", user.email if user else None)
            print("Password entered:", password)

            if user:
                print("Stored hash:", user.password_hash)
                print("Password match:", verify_password(password, user.password_hash))

            if not user or not verify_password(password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            return create_access_token_for_user(user, tenant=tenant)