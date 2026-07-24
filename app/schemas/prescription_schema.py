import os
import shutil
import uuid
from datetime import date

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pharmacy import Prescription, Patient

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

UPLOAD_DIR = "app/upload/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf"
}

@router.post("/upload")
async def upload_prescription(
    doctor_name: str = Form(...),
    registration_no: str = Form(...),
    prescription_date: date = Form(...),
    patient_name: str = Form(...),
    mobile: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, or PDF files are allowed"
        )

    if not registration_no or len(registration_no) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor registration number"
        )

    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    patient = Patient(
        name=patient_name,
        mobile=mobile
    )
    db.add(patient)
    await db.flush()

    prescription = Prescription(
        doctor_name=doctor_name,
        registration_no=registration_no,
        prescription_date=prescription_date,
        image_path=file_path,
        patient_id=patient.id
    )
    db.add(prescription)

    await db.commit()

    return {
        "prescription_id": prescription.id,
        "file_type": file.content_type,
        "message": "Prescription uploaded successfully"
    }
