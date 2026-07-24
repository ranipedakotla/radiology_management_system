# import os
# import shutil
# import uuid
# from datetime import date
# from typing import Optional
#
# from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import get_db
# from app.models.pharmacy import Patient
# from app.models.hospital import Hospital
#
# from app.models.user_models import User,Prescription
# from app.utils.rolebased_security import get_current_user
#
# router = APIRouter(
#     prefix="/prescriptions",
#     tags=["Prescriptions"]
# )
#
# UPLOAD_DIR = "app/upload/prescriptions"
# os.makedirs(UPLOAD_DIR, exist_ok=True)
#
# # ALLOW ALL COMMON PRESCRIPTION FILE TYPES
# ALLOWED_TYPES = {
#     "image/jpeg",
#     "image/png",
#     "image/jpg",
#     "application/pdf"
# }
#
# @router.post("/upload")
# async def upload_prescription(
#     file: UploadFile = File(...),
#     doctor_name: Optional[str] = Form(None),
#     registration_no: Optional[str] = Form(None),
#     prescription_date: Optional[date] = Form(None),
#     patient_name: Optional[str] = Form(None),
#     mobile: Optional[int] = Form(None),
#     branch_id: Optional[int] = Form(None),
#     hospital_id: Optional[int] = Form(None),
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # -------------------------------
#     # FILE TYPE VALIDATION
#     # -------------------------------
#
#
#
#
#     if file.content_type not in ALLOWED_TYPES:
#         raise HTTPException(
#             status_code=400,
#             detail="Only JPG, PNG, or PDF files are allowed"
#         )
#
#     # -------------------------------
#     # BASIC DOCTOR VALIDATION
#     # -------------------------------
#     if not registration_no or len(registration_no) < 3:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid doctor registration number"
#         )
#
#     # -------------------------------
#     # SAVE FILE SAFELY
#     # -------------------------------
#     safe_filename = f"{uuid.uuid4()}_{file.filename}"
#     file_path = os.path.join(UPLOAD_DIR, safe_filename)
#
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#
#     # -------------------------------
#     # CREATE PATIENT
#     # -------------------------------
#     patient = Patient(
#         name=patient_name,
#         mobile=mobile,
#         # hospital_id=hospital_id,
#         # branch_id=branch_id,
#     )
#     db.add(patient)
#     await db.flush()
#
#     # -------------------------------
#     # CREATE PRESCRIPTION
#     # -------------------------------
#     prescription = Prescription(
#         doctor_name=doctor_name,
#         registration_no=registration_no,
#         prescription_date=prescription_date,
#         filename=safe_filename,
#         content_type=file.content_type,
#         file_path=file_path,
#
#         image_path=file_path,
#         patient_id=patient.id,
#         pharmacist_id = current_user.id,
#         branch_id=branch_id,
#         hospital_id=hospital_id
#     )
#     db.add(prescription)
#
#     await db.commit()
#     await db.refresh(prescription)
#
#     return {
#         "prescription_id": prescription.id,
#         "file_type": file.content_type,
#         "hospital_id": prescription.hospital_id,
#         "branch_id": prescription.branch_id,
#         "message": "Prescription uploaded successfully"
#     }
#