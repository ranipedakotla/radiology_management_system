from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class RadiologyReport(Base):
    __tablename__ = "radiology_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, index=True, nullable=False)

    # Hospital
    hospital_department = Column(String(255), nullable=True)

    # Patient
    patient_name = Column(String(255), nullable=False)
    patient_uhid = Column(String(100), nullable=False)
    patient_age = Column(Integer, nullable=False)
    patient_gender = Column(String(20), nullable=False)
    referring_doctor = Column(String(255), nullable=True)
    patient_department = Column(String(255), nullable=True)

    # Study
    study_date = Column(String(20), nullable=False)
    study_time = Column(String(20), nullable=False)
    report_date = Column(String(20), nullable=False)
    report_time = Column(String(20), nullable=False)
    modality = Column(String(50), nullable=False)
    test_name = Column(String(255), nullable=False)
    body_part = Column(String(100), nullable=True)

    # Content
    clinical_history = Column(Text, nullable=True)
    findings = Column(JSON, nullable=False)        # [{"label": "...", "text": "..."}]
    impression = Column(JSON, nullable=False)       # ["point 1", "point 2"]
    recommendations = Column(Text, nullable=True)

    # Radiologist / signature
    radiologist_name = Column(String(255), nullable=False)
    radiologist_credentials = Column(String(255), nullable=True)
    radiologist_title = Column(String(255), nullable=True)
    radiologist_reg_no = Column(String(100), nullable=True)
    signature_data_uri = Column(Text, nullable=True)

    # PDF
    pdf_s3_key = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())