# from argon2 import hash_password
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, func
# from sqlalchemy.orm import Session
# from starlette import status
# from app.core.security import get_db
# from app.models.auth import User
# from app.schemas.rolebased_schemas import UserCreate, UserOut, Token
# from app.utils.rolebased_security import (
#     get_password_hash,
#     verify_password,
#     create_access_token,
#     create_session_id,
#     role_required
# )
#
#
# router = APIRouter()
#
#
# # @router.post("/register", response_model=UserOut)
# # async def register_user(user_in: UserCreate,db: AsyncSession = Depends(get_db)):
# #     role_upper = user_in.role.strip().upper()
#
#
# #     if role_upper == "SUPERADMIN":
# #         res = await db.execute(select(User).where(User.role == "SUPERADMIN"))
# #         if res.scalar_one_or_none():
# #             raise HTTPException(status_code=400, detail="Only one SUPERADMIN allowed")
#
# #     #5 pharmacists max
# #     if role_upper == "PHARMACIST":
# #         res = await db.execute(
# #             select(func.count()).select_from(User).where(User.role == "PHARMACIST")
# #         )
# #         pharm_count = res.scalar_one() or 0
# #         if pharm_count >= 5:
# #             raise HTTPException(
# #                 status_code=400,
# #                 detail="Maximum 5 PHARMACIST users allowed",
# #             )
#
#
# #     res = await db.execute(select(User).where(User.username == user_in.username))
# #     existing = res.scalar_one_or_none()
# #     if existing:
# #         raise HTTPException(status_code=400, detail="Username already registered")
#
# #     user = User(
# #         username=user_in.username,
# #         email=user_in.email,
# #         role=role_upper,
# #         hashed_password=get_password_hash(user_in.password),
# #     )
# #     db.add(user)
# #     await db.commit()
# #     await db.refresh(user)
# #     return user
#
#
# # @router.post("/token", response_model=Token)
# # async def login(form_data: OAuth2PasswordRequestForm = Depends(),db: AsyncSession = Depends(get_db)):
# #     res = await db.execute(select(User).where(User.username == form_data.username))
# #     user = res.scalar_one_or_none()
# #     if not user or not verify_password(form_data.password, user.hashed_password):
# #         raise HTTPException(status_code=401, detail="Incorrect username or password")
#
# #     session_id = create_session_id()
# #     user.active_session_id = session_id
# #     await db.commit()
#
# #     token = create_access_token(
# #         {"sub": user.username, "role": user.role, "sid": session_id}
# #     )
# #     return Token(access_token=token)
#
#
#
#
# @router.post("/register-initial-superadmin", response_model=UserOut)
# async def register_initial_superadmin(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
#     role_upper = user_in.role.strip().upper()
#
#
#     if role_upper != "SUPERADMIN":
#         raise HTTPException(
#             status_code=400,
#             detail="Only SUPERADMIN can be registered via this endpoint"
#         )
#
#     # Check if SUPERADMIN already exists
#     res = await db.execute(select(User).where(User.role == "SUPERADMIN"))
#     if res.scalar_one_or_none():
#         raise HTTPException(
#             status_code=400,
#             detail="SUPERADMIN already exists. Use /token to login."
#         )
#
#     # Check username uniqueness
#     res = await db.execute(select(User).where(User.username == user_in.username))
#     if res.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Username already registered")
#
#     user = User(
#         username=user_in.username,
#         email=user_in.email,
#         role=role_upper,
#         hashed_password=get_password_hash(user_in.password),
#     )
#     db.add(user)
#     await db.commit()
#     await db.refresh(user)
#     return user
#
#
# @router.post("/token", response_model=Token)
# async def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: AsyncSession = Depends(get_db)
# ):
#     res = await db.execute(select(User).where(User.username == form_data.username))
#     user = res.scalar_one_or_none()
#
#     if not user or not verify_password(form_data.password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     session_id = create_session_id()
#     user.active_session_id = session_id
#     await db.commit()
#
#     token = create_access_token({
#         "sub": user.username,
#         "role": user.role,
#         "sid": session_id
#     })
#     return Token(access_token=token, token_type="bearer")