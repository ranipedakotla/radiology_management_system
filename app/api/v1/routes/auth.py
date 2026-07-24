from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
# from sqlalchemy import select
# from sqlalchemy import or_
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.orm import Session
# from app.core.security import get_db
# from app.models.auth import User
from app.schemas.auth import Token,LoginIn
from app.services.auth import AuthService
# from app.utils.rolebased_security import create_session_id, create_access_token
# from argon2 import PasswordHasher
# from argon2.exceptions import VerifyMismatchError

# ph = PasswordHasher()

router = APIRouter()

security = HTTPBearer()

@router.post("/login", response_model=Token)
async def login(payload: LoginIn):

    email = payload.email
    password = payload.password

    token = await AuthService().login(email, password)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# @router.post("/login", response_model=Token)
# async def login(
#     payload: LoginIn,
#     db: Session = Depends(get_db),
# ):
#     result = db.execute(
#         select(User).where(
#             or_(
#                 User.email == payload.email
#             )
#         )
#     )
#
#
#     user = result.scalar_one_or_none()
#
#     if not user:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid credentials"
#         )
#
#     try:
#         ph.verify(user.password_hash, payload.password)
#     except VerifyMismatchError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid credentials"
#         )
#
#     session_id = create_session_id()
#     user.active_session_id = session_id
#
#     db.commit()
#
#     token = create_access_token(
#         {
#             "sub": str(user.id),
#             "username": user.username,
#             "email": user.email,
#             "role": user.role,
#             "hospital_id": user.hospital_id,
#             "branch_id": user.current_branch_id,
#             "sid": session_id,
#         }
#     )
#
#     return {
#         "access_token": token,
#         "token_type": "bearer",
#     }
