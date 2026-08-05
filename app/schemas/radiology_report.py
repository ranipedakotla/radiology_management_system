from typing import List, Optional
from pydantic import BaseModel


class FindingItem(BaseModel):
    label: str
    text: str


class RadiologyReportCreate(BaseModel):
    report_id: str

    hospital_department: Optional[str] = None

    patient_name: str
    patient_uhid: str
    patient_age: int
    patient_gender: str
    referring_doctor: Optional[str] = None
    patient_department: Optional[str] = None

    study_date: str
    study_time: str
    report_date: str
    report_time: str
    modality: str
    test_name: str
    body_part: Optional[str] = None

    clinical_history: Optional[str] = None
    findings: List[FindingItem]
    impression: List[str]
    recommendations: Optional[str] = None

    radiologist_name: str
    radiologist_credentials: Optional[str] = None
    radiologist_title: Optional[str] = None
    radiologist_reg_no: Optional[str] = None
    signature_data_uri: Optional[str] = None


class RadiologyReportOut(BaseModel):
    id: int
    report_id: str
    patient_name: str
    pdf_s3_key: Optional[str] = None

    class Config:
        from_attributes = True