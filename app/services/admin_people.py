from __future__ import annotations

import re
from typing import Iterable
from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import select, text, and_, func
from sqlalchemy.orm import Session

from app.schemas.admin_people import StaffCreateIn, PatientCreateIn, UserCreateIn, StaffUpdate
from app.utils.tenant import Tenant

# from app.schemas.admin_people import StaffCreate
from app.models.auth import User, Role
from app.models.people import (
    Patient, Staff, Doctor,
    PatientBranchCode, StaffBranch, DoctorBranch,
)
from app.core.idgen import next_code, PREFIX_PATIENT, PREFIX_STAFF, PREFIX_DOCTOR
from app.utils.s3 import upload_to_s3

# pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd = CryptContext(schemes=["argon2"], deprecated="auto")

ALLOWED_STAFF_ROLES = {
    "receptionist", "front_office", "pharmacist", "pathologist",
    "radiologist", "accountant", "nurse", "admin", "branch_admin",
    "pharmacy_admin", "pathology_admin", "radiology_admin", "doctor","lab_tech","blood_bank_staff","driver"
}


# ------------------------- small helpers & validations -------------------------

def _bad(msg: str, code: int = 400) -> HTTPException:
    return HTTPException(status_code=code, detail=msg)


def _normalize_phone(s: str | None) -> str:
    # keep digits only; store empty string if none
    return re.sub(r"\D+", "", s or "")


def _ensure_email_unique(db: Session, email: str):
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        raise _bad("Email already exists")


def _ensure_phone_unique(db: Session, phone: str):
    if db.execute(select(User).where(User.phone == phone)).scalar_one_or_none():
        raise _bad("phone number already exists")


def _role_ids(db: Session, role_names: Iterable[str]) -> dict[str, int]:
    names = [r for r in role_names]
    if not names:
        return {}
    rows = db.execute(select(Role.id, Role.name).where(Role.name.in_(names))).all()
    found_by_name = {name: rid for rid, name in rows}
    missing = [n for n in names if n not in found_by_name]
    if missing:
        raise _bad(f"Unknown roles: {', '.join(missing)}")
    return found_by_name


def _require_create_user_fields(payload):
    if not payload.email or not payload.password:
        raise _bad("email & password are required when create_user=true")
    if len(payload.password) < 6:
        raise _bad("password must be at least 6 characters")


def _fee(value: int | None) -> int:
    v = int(value or 0)
    if v < 0:
        raise _bad("consultation_fee cannot be negative")
    return v


def _find_duplicate_patient(db: Session, tenant: Tenant, *, first_name: str, last_name: str, dob,
                            phone_number: str | None):
    """
    Returns (patient, reason) if duplicate exists, else (None, None).
    """
    if phone_number:
        patient = db.execute(
            select(Patient).where(
                and_(Patient.hospital_id == tenant.hospital_id,
                     Patient.phone_number == phone_number)
            )
        ).scalar_one_or_none()
        if patient:
            return patient, "phone number already exists"

    # fallback rule: match on name + dob
    patient = db.execute(
        select(Patient).where(
            and_(
                Patient.hospital_id == tenant.hospital_id,
                Patient.first_name == first_name,
                Patient.last_name == last_name,
                Patient.dob == dob,
            )
        )
    ).scalar_one_or_none()
    if patient:
        return patient, "patient with same name and date of birth already exists"

    return None, None


def _normalize_pan(pan: str | None) -> str | None:
    if not pan:
        return None
    return pan.strip().upper()


# ------------------------------ service class --------------------------------

class AdminPeopleService:
    def __init__(self, db: Session, tenant: Tenant) -> None:
        self.db = db
        self.tenant = tenant

    def _apply_tenant(self, obj, *, branch_id: int | None = None):
        """
        Option-B: master records are hospital-scoped.
        We only stamp hospital_id here; branch membership goes via link tables.
        """
        if hasattr(obj, "hospital_id"):
            obj.hospital_id = self.tenant.hospital_id
        if hasattr(obj, "branch_id"):
            obj.branch_id = branch_id or self.tenant.branch_id
        # DO NOT set obj.branch_id here for Staff/Doctor/Patient

    def create_patient(self, payload, aadhaar_file_path: str = ""):
        phone_number = _normalize_phone(payload.phone_number)

        # Phone number duplicate
        if phone_number:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.phone_number == phone_number,
                    Patient.hospital_id == self.tenant.hospital_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Phone number already exists"
                )

        # Aadhaar duplicate
        if payload.aadhaar_no:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.aadhaar_no == payload.aadhaar_no,
                    Patient.hospital_id == self.tenant.hospital_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Aadhaar number already exists"
                )

        # Email duplicate
        if payload.email:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.email == payload.email,
                    Patient.hospital_id == self.tenant.hospital_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Email already exists"
                )

        dup, reason = _find_duplicate_patient(
            self.db,
            self.tenant,
            first_name=(payload.first_name or "").strip(),
            last_name=(payload.last_name or "").strip(),
            dob=payload.dob,
            phone_number=phone_number,
        )

        if dup:
            raise _bad(reason, 409)

        # Create new patient
        p = Patient(
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            phone_number=phone_number,

            guardian_name=payload.guardian_name,
            gender=payload.gender,
            age=payload.age,
            blood_group=payload.blood_group,
            marital_status=payload.marital_status,
            email=payload.email,
            location=payload.location,
            reason=payload.reason,
            aadhaar_no=payload.aadhaar_no,
            aadhaar_file_path=aadhaar_file_path or None,

            patient_uid=next_code(self.db, PREFIX_PATIENT),
            patient_code=next_code(self.db, PREFIX_PATIENT),
        )

        self._apply_tenant(p)
        self.db.add(p)
        self.db.flush()

        code = self._ensure_patient_branch_code(
            p.id,
            self.tenant.branch_id
        )

        self.db.commit()

        return {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "patient_code": code,
            "phone_number": p.phone_number,

            "guardian_name": p.guardian_name,
            "gender": p.gender,
            "age": p.age,
            "blood_group": p.blood_group,
            "marital_status": p.marital_status,
            "email": p.email,
            "location": p.location,
            "reason": p.reason,
            "aadhaar_no": p.aadhaar_no,
            "aadhaar_file_path": p.aadhaar_file_path,
        }

    def update_patient(
            self,
            patient_id: int,
            payload: PatientCreateIn,
            aadhaar_file_path: str | None = None,
    ):
        if patient_id is None:
            raise HTTPException(
                status_code=400,
                detail="Patient ID cannot be null"
            )

        patient = self.db.get(Patient, patient_id)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found"
            )

        phone_number = _normalize_phone(payload.phone_number)

        # Phone number duplicate
        if phone_number:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.phone_number == phone_number,
                    Patient.hospital_id == self.tenant.hospital_id,
                    Patient.id != patient_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Phone number already exists"
                )

        # Aadhaar duplicate
        if payload.aadhaar_no:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.aadhaar_no == payload.aadhaar_no,
                    Patient.hospital_id == self.tenant.hospital_id,
                    Patient.id != patient_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Aadhaar number already exists"
                )

        # Email duplicate
        if payload.email:
            existing = self.db.execute(
                select(Patient).where(
                    Patient.email == payload.email,
                    Patient.hospital_id == self.tenant.hospital_id,
                    Patient.id != patient_id
                )
            ).scalars().first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Email already exists"
                )

        patient.first_name = payload.first_name
        patient.last_name = payload.last_name
        patient.dob = payload.dob
        patient.phone_number = payload.phone_number
        patient.guardian_name = payload.guardian_name
        patient.gender = payload.gender
        patient.age = payload.age
        patient.blood_group = payload.blood_group
        patient.marital_status = payload.marital_status
        patient.email = payload.email
        patient.location = payload.location
        patient.reason = payload.reason
        patient.aadhaar_no = payload.aadhaar_no

        if aadhaar_file_path:
            patient.aadhaar_file_path = aadhaar_file_path

        self.db.commit()
        self.db.refresh(patient)

        return patient

    def delete_patient(self, patient_id: int):

        patient = self.db.get(Patient, patient_id)

        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient not found"
            )

        try:
            self.db.delete(patient)
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Cannot delete patient because related records exist"
            )

    def _ensure_patient_branch_code(self, patient_id: int, branch_id: int) -> str:
        row = self.db.execute(
            select(PatientBranchCode).where(
                PatientBranchCode.patient_id == patient_id,
                PatientBranchCode.branch_id == branch_id,
            )
        ).scalar_one_or_none()
        if row:
            return row.code
        code = next_code(self.db, PREFIX_PATIENT)
        self.db.add(PatientBranchCode(patient_id=patient_id, branch_id=branch_id, code=code))
        self.db.flush()
        return code

    def add_patient_to_branch(self, patient_id: int, branch_id: int):
        p = self.db.get(Patient, patient_id)
        if not p or p.hospital_id != self.tenant.hospital_id:
            raise _bad("Patient not found", 404)
        code = self._ensure_patient_branch_code(patient_id, branch_id)
        self.db.commit()
        return {"patient_id": patient_id, "branch_id": branch_id, "code": code}

    def create_doctor(self, payload, profile_pic_url: str | None = None,
                      signature_url: str | None = None,
                      license_file_url: str | None = None, ):
        pan_number = _normalize_pan(payload.pan_number)

        if pan_number:
            if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan_number):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PAN number format. Example: ABCDE1234F"
                )

        if payload.aadhar_number:
            aadhar = str(payload.aadhar_number).strip()

            if len(aadhar) != 12:
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must be exactly 12 digits"
                )

            if not aadhar.isdigit():
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must contain only digits"
                )

        phone_number = _normalize_phone(payload.phone)

        existing_phone_staff = (
            self.db.query(Staff)
            .filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.phone_number == phone_number
            )
            .first()
        )

        if existing_phone_staff:
            raise HTTPException(
                status_code=400,
                detail=f"Phone number {phone_number} already exists"
            )

        if payload.aadhar_number:
            existing_aadhar_staff = (
                self.db.query(Staff)
                .filter(
                    Staff.hospital_id == self.tenant.hospital_id,
                    Staff.aadhar_number == payload.aadhar_number
                )
                .first()
            )

            if existing_aadhar_staff:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aadhaar number {payload.aadhar_number} already exists"
                )

            existing_aadhar_doctor = (
                self.db.query(Doctor)
                .filter(
                    Doctor.hospital_id == self.tenant.hospital_id,
                    Doctor.aadhar == payload.aadhar_number
                )
                .first()
            )

            if existing_aadhar_doctor:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aadhaar number {payload.aadhar_number} already exists"
                )

        existing_email_staff = (
            self.db.query(Staff)
            .filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.lower(Staff.email) == payload.email.lower()
            )
            .first()
        )

        if existing_email_staff:
            raise HTTPException(
                status_code=400,
                detail=f"Email {payload.email} already exists with another staff/doctor"
            )

        existing_email_user = (
            self.db.query(User)
            .filter(
                func.lower(User.email) == payload.email.lower()
            )
            .first()
        )

        if existing_email_user:
            raise HTTPException(
                status_code=400,
                detail=f"Email {payload.email} already exists"
            )

        existing_staff = (
            self.db.query(Staff)
            .filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.upper(Staff.pan_number) == pan_number
            )
            .first()
        )

        if existing_staff:
            raise HTTPException(
                status_code=400,
                detail=f"PAN number {pan_number} already exists with another staff/doctor"
            )

        existing_doctor = (
            self.db.query(Doctor)
            .filter(
                Doctor.hospital_id == self.tenant.hospital_id,
                func.upper(Doctor.pan) == pan_number
            )
            .first()
        )

        if existing_doctor:
            raise HTTPException(
                status_code=400,
                detail=f"PAN number {pan_number} already exists with another doctor"
            )

        st = Staff(
            employee_id=next_code(self.db, PREFIX_STAFF),
            staff_code=next_code(self.db, PREFIX_STAFF),

            first_name=payload.first_name,
            last_name=payload.last_name,
            full_name=f"{payload.first_name} {payload.last_name or ''}".strip(),

            email=payload.email,
            phone_number=payload.phone,
            uan_number=payload.uan_number,
            esi_number=payload.esi_number,

            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_number=payload.emergency_contact_number,

            gender=payload.gender,
            date_of_birth=payload.date_of_birth,

            address_city=payload.address_city,
            address_state=payload.address_state,
            address_pincode=payload.address_pincode,
            address_country="India",

            department=payload.department,
            designation=payload.designation or "Doctor",
            joining_date=payload.joining_date,

            role="doctor",
            qualification=payload.qualification,
            experience_years=payload.experience,
            monthly_salary=payload.monthly_salary,

            pan_number=pan_number,
            aadhar_number=payload.aadhar_number,

            bank_account_holder_name=payload.bank_account_holder_name,
            bank_account_number=payload.bank_account_number,
            bank_ifsc_code=payload.bank_ifsc_code,
            bank_name=payload.bank_name,

            is_active=True,
        )

        self._apply_tenant(st)
        self.db.add(st)
        self.db.flush()

        doc = Doctor(
            staff_id=st.id,
            consultation_fee=_fee(payload.consultation_fee),
            pan=pan_number,
            aadhar=payload.aadhar_number,
            bank=payload.bank_name,
            account_no=payload.bank_account_number,
            ifsc=payload.bank_ifsc_code,
            floor_location=payload.floor_location,
            shift_start=payload.shift_start,
            shift_end=payload.shift_end,

            specialty=(payload.specialty or ""),
            specialization=payload.specialization,
            designation=(payload.designation or None),
            doctor_code=next_code(self.db, PREFIX_DOCTOR),
            department=(payload.department or ""),
        )

        self._apply_tenant(doc)
        self.db.add(doc)
        self.db.flush()

        if profile_pic_url:
            doc.profile_pic_url = profile_pic_url

        if signature_url:
            doc.signature_url = signature_url

        if license_file_url:
            doc.license_url = license_file_url

        self._ensure_staff_branch(st.id, self.tenant.branch_id)
        self._ensure_doctor_branch(doc.id, self.tenant.branch_id)

        user_id: int | None = None

        if payload.create_user:
            _require_create_user_fields(payload)
            _ensure_email_unique(self.db, payload.email)
            _ensure_phone_unique(self.db, payload.phone)

            u = User(
                email=payload.email,
                phone=_normalize_phone(payload.phone),
                password_hash=pwd.hash(payload.password),
                is_active=True,
                hospital_id=self.tenant.hospital_id,
                current_branch_id=self.tenant.branch_id,
            )

            self.db.add(u)
            self.db.flush()
            user_id = u.id

            rid = _role_ids(self.db, ["doctor"])["doctor"]

            self.db.execute(
                text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
                {"u": user_id, "r": rid},
            )

            st.user_id = user_id
            self.db.flush()

        self.db.commit()

        return {
            "id": doc.id,
            "doctor_code": doc.doctor_code,

            "first_name": st.first_name,
            "last_name": st.last_name,

            "staff_id": st.id,
            "staff_code": st.staff_code,
            "user_id": st.user_id,

            "profile_pic_url": doc.profile_pic_url,
            "consultation_fee": doc.consultation_fee,

            "specialty": doc.specialty,
            "designation": doc.designation,
            "department": doc.department,
            "specialization": doc.specialization,

            "signature_url": doc.signature_url,
            "license_url": doc.license_url,

            "uan_number": st.uan_number,
            "esi_number": st.esi_number,

            "pan": doc.pan,
            "aadhar": doc.aadhar,

            "bank": doc.bank,
            "account_no": doc.account_no,
            "ifsc": doc.ifsc,

            "floor_location": doc.floor_location,

            "qualification": st.qualification,

            "shift_start": doc.shift_start,
            "shift_end": doc.shift_end,

            "gender": st.gender,
            "email": st.email,
            "phone_number": st.phone_number,

            "date_of_birth": st.date_of_birth,

            "address_city": st.address_city,
            "address_street": st.address_street,
            "address_state": st.address_state,
            "address_pincode": st.address_pincode,
            "address_country": st.address_country,

            "experience": st.experience_years,
        }

    def get_doctor_by_id(self, doctor_id: int):
        doctor = (
            self.db.query(Doctor)
            .filter(
                Doctor.id == doctor_id,
                Doctor.hospital_id == self.tenant.hospital_id,
                Doctor.branch_id == self.tenant.branch_id,
            )
            .first()
        )

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found"
            )

        return doctor

    def _ensure_doctor_branch(self, doctor_id: int, branch_id: int):
        existing = self.db.execute(
            select(DoctorBranch).where(
                DoctorBranch.doctor_id == doctor_id,
                DoctorBranch.branch_id == branch_id
            )
        ).scalar_one_or_none()

        if not existing:
            self.db.add(
                DoctorBranch(
                    doctor_id=doctor_id,
                    branch_id=branch_id
                )
            )
            self.db.flush()

    def _ensure_staff_branch(self, staff_id, branch_id):
        existing = self.db.execute(
            select(StaffBranch).where(
                StaffBranch.staff_id == staff_id,
                StaffBranch.branch_id == branch_id
            )
        ).scalar_one_or_none()

        if not existing:
            sb = StaffBranch(
                staff_id=staff_id,
                branch_id=branch_id
            )
        self.db.add(sb)
        self.db.flush()

    def _ensure_doctor_branch(self, doctor_id: int, branch_id: int):

        existing = self.db.execute(
            select(DoctorBranch).where(
                DoctorBranch.doctor_id == doctor_id,
                DoctorBranch.branch_id == branch_id
            )
        ).scalar_one_or_none()

        if not existing:
            self.db.add(
                DoctorBranch(
                    doctor_id=doctor_id,
                    branch_id=branch_id
                )
            )

            self.db.flush()

    def update_doctor(
            self,
            doctor_id: int,

            first_name=None,
            last_name=None,

            consultation_fee=None,
            specialty=None,
            designation=None,
            department=None,
            specialization=None,
            experience=None,

            email=None,
            phone=None,
            gender=None,
            date_of_birth=None,

            emergency_contact_name=None,
            emergency_contact_number=None,

            address_city=None,
            address_state=None,
            address_pincode=None,

            joining_date=None,
            qualification=None,
            monthly_salary=None,
            shift_type=None,
            shift_start=None,
            shift_end=None,

            pan_number=None,
            aadhar_number=None,
            uan_number=None,
            esi_number=None,
            floor_location=None,

            bank_account_holder_name=None,
            bank_account_number=None,
            bank_ifsc_code=None,
            bank_name=None,

            profile_pic=None,
            signature=None,
            license_file=None,
            password=None
    ):

        doctor = self.db.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.hospital_id == self.tenant.hospital_id,
            Doctor.branch_id == self.tenant.branch_id,
        ).first()

        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        staff = self.db.get(Staff, doctor.staff_id)

        if password and staff.user_id:
            user = self.db.get(User, staff.user_id)

            if user:
                user.password_hash = pwd.hash(password)

        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        if email is not None:
            existing_staff = (
                self.db.query(Staff)
                .filter(
                    Staff.hospital_id == self.tenant.hospital_id,
                    func.lower(Staff.email) == email.lower(),
                    Staff.id != staff.id
                )
                .first()
            )

            if existing_staff:
                raise HTTPException(
                    status_code=400,
                    detail=f"Email {email} already exists"
                )

            existing_user = (
                self.db.query(User)
                .filter(
                    func.lower(User.email) == email.lower(),
                    User.id != staff.user_id
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail=f"Email {email} already exists"
                )

        # Phone validation + duplicate check
        if phone is not None:
            phone = _normalize_phone(phone)

            if not (phone.isdigit() and len(phone) == 10):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number must contain exactly 10 digits"
                )

            existing_phone = (
                self.db.query(Staff)
                .filter(
                    Staff.hospital_id == self.tenant.hospital_id,
                    Staff.phone_number == phone,
                    Staff.id != staff.id
                )
                .first()
            )

            if existing_phone:
                raise HTTPException(
                    status_code=400,
                    detail=f"Phone number {phone} already exists"
                )

        # PAN validation + duplicate check
        if pan_number is not None:
            pan_number = _normalize_pan(pan_number)

            if not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan_number):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid PAN number format. Example: ABCDE1234F"
                )

            existing_pan_staff = (
                self.db.query(Staff)
                .filter(
                    Staff.hospital_id == self.tenant.hospital_id,
                    func.upper(Staff.pan_number) == pan_number,
                    Staff.id != staff.id
                )
                .first()
            )

            if existing_pan_staff:
                raise HTTPException(
                    status_code=400,
                    detail=f"PAN number {pan_number} already exists"
                )

            existing_pan_doctor = (
                self.db.query(Doctor)
                .filter(
                    Doctor.hospital_id == self.tenant.hospital_id,
                    func.upper(Doctor.pan) == pan_number,
                    Doctor.id != doctor.id
                )
                .first()
            )

            if existing_pan_doctor:
                raise HTTPException(
                    status_code=400,
                    detail=f"PAN number {pan_number} already exists"
                )

        # Aadhaar validation + duplicate check
        if aadhar_number is not None:
            aadhar_number = str(aadhar_number).strip()

            if len(aadhar_number) != 12:
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must be exactly 12 digits"
                )

            if not aadhar_number.isdigit():
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must contain only digits"
                )

            existing_aadhar_staff = (
                self.db.query(Staff)
                .filter(
                    Staff.hospital_id == self.tenant.hospital_id,
                    Staff.aadhar_number == aadhar_number,
                    Staff.id != staff.id
                )
                .first()
            )

            if existing_aadhar_staff:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aadhaar number {aadhar_number} already exists"
                )

            existing_aadhar_doctor = (
                self.db.query(Doctor)
                .filter(
                    Doctor.hospital_id == self.tenant.hospital_id,
                    Doctor.aadhar == aadhar_number,
                    Doctor.id != doctor.id
                )
                .first()
            )

            if existing_aadhar_doctor:
                raise HTTPException(
                    status_code=400,
                    detail=f"Aadhaar number {aadhar_number} already exists"
                )

        # ---------------- Staff Update ---------------- #

        if first_name is not None:
            staff.first_name = first_name

        if last_name is not None:
            staff.last_name = last_name

        staff.full_name = f"{staff.first_name} {staff.last_name or ''}".strip()

        if email is not None:
            staff.email = email

        if phone is not None:
            staff.phone_number = phone

        if gender is not None:
            staff.gender = gender

        if experience is not None:
            staff.experience_years = experience

        if date_of_birth is not None:
            staff.date_of_birth = date_of_birth

        if emergency_contact_name is not None:
            staff.emergency_contact_name = emergency_contact_name

        if emergency_contact_number is not None:
            staff.emergency_contact_number = emergency_contact_number

        if address_city is not None:
            staff.address_city = address_city

        if address_state is not None:
            staff.address_state = address_state

        if address_pincode is not None:
            staff.address_pincode = address_pincode

        if joining_date is not None:
            staff.joining_date = joining_date

        if qualification is not None:
            staff.qualification = qualification

        if monthly_salary is not None:
            staff.monthly_salary = monthly_salary

        if shift_type is not None:
            staff.shift_type = shift_type

        if shift_start is not None:
            doctor.shift_start = shift_start

        if shift_end is not None:
            doctor.shift_end = shift_end

        if pan_number is not None:
            staff.pan_number = pan_number

        if aadhar_number is not None:
            staff.aadhar_number = aadhar_number

        if bank_account_holder_name is not None:
            staff.bank_account_holder_name = bank_account_holder_name

        if bank_account_number is not None:
            staff.bank_account_number = bank_account_number

        if bank_ifsc_code is not None:
            staff.bank_ifsc_code = bank_ifsc_code

        if bank_name is not None:
            staff.bank_name = bank_name

        # ---------------- Doctor Update ---------------- #

        if consultation_fee is not None:
            doctor.consultation_fee = consultation_fee

        if specialty is not None:
            doctor.specialty = specialty

        if designation is not None:
            doctor.designation = designation
            staff.designation = designation

        if department is not None:
            doctor.department = department
            staff.department = department

        if specialization is not None:
            doctor.specialization = specialization

        # Optional duplicate HR details in doctor table
        if pan_number is not None:
            doctor.pan = pan_number

        if aadhar_number is not None:
            doctor.aadhar = aadhar_number

        if bank_name is not None:
            doctor.bank = bank_name

        if bank_account_number is not None:
            doctor.account_no = bank_account_number

        if bank_ifsc_code is not None:
            doctor.ifsc = bank_ifsc_code

        if uan_number is not None:
            staff.uan_number = uan_number

        if esi_number is not None:
            staff.esi_number = esi_number

        if floor_location is not None:
            doctor.floor_location = floor_location

        # ---------------- Files ---------------- #

        if profile_pic:
            doctor.profile_pic_url = profile_pic

        if signature:
            doctor.signature_url = signature

        if license_file:
            doctor.license_url = license_file

        self.db.commit()
        self.db.refresh(doctor)
        self.db.refresh(staff)

        return {
            "id": doctor.id,
            "doctor_code": doctor.doctor_code,

            "first_name": staff.first_name,
            "last_name": staff.last_name,

            "staff_id": staff.id,
            "staff_code": staff.staff_code,
            "user_id": staff.user_id,

            "profile_pic_url": doctor.profile_pic_url,
            "consultation_fee": doctor.consultation_fee,
            "specialty": doctor.specialty,
            "designation": doctor.designation,
            "department": doctor.department,
            "specialization": doctor.specialization,
            "shift_type": staff.shift_type,
            "shift_start": doctor.shift_start,
            "shift_end": doctor.shift_end,
            "signature_url": doctor.signature_url,
            "license_url": doctor.license_url,

            "uan_number": staff.uan_number,
            "esi_number": staff.esi_number,
            "pan": doctor.pan,
            "aadhar": doctor.aadhar,
            "bank": doctor.bank,
            "account_no": doctor.account_no,
            "ifsc": doctor.ifsc,
            "floor_location": doctor.floor_location,
        }

    def delete_doctor(self, doctor_id: int):

        doctor = self.db.query(Doctor).filter(
            Doctor.id == doctor_id,
            Doctor.hospital_id == self.tenant.hospital_id,
            Doctor.branch_id == self.tenant.branch_id,
        ).first()

        if not doctor:
            return None

        doctor.is_active = False

        self.db.commit()

        return {"message": "Doctor deactivated successfully"}


class StaffService:
    def __init__(self, db: Session, tenant: Tenant):
        self.db = db
        self.tenant = tenant

    def _apply_tenant(self, obj):
        if hasattr(obj, "hospital_id"):
            obj.hospital_id = self.tenant.hospital_id

        if hasattr(obj, "branch_id"):
            obj.branch_id = self.tenant.branch_id

    def create_staff(
            self,
            payload: StaffCreateIn,
            id_proof=None,
            address_proof=None,
            educational_certificates=None,
            experience_letters=None,
            profile_photo=None,
            signature=None,
    ):
        phone_number = _normalize_phone(payload.phone_number)
        pan_number = _normalize_pan(payload.pan_number) if payload.pan_number else None

        # Phone validation
        if phone_number:
            if not (phone_number.isdigit() and len(phone_number) == 10):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number must contain exactly 10 digits"
                )

        # PAN validation
        if pan_number:
            if len(pan_number) > 10:
                raise HTTPException(
                    status_code=400,
                    detail="PAN number cannot exceed 10 characters"
                )

        # Aadhaar validation
        if payload.aadhar_number:
            aadhar = str(payload.aadhar_number).strip()

            if not (aadhar.isdigit() and len(aadhar) == 12):
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must contain exactly 12 digits"
                )

        # UAN validation
        if payload.uan_number:
            uan = str(payload.uan_number).strip()

            if len(uan) > 12:
                raise HTTPException(
                    status_code=400,
                    detail="UAN number cannot exceed 12 digits"
                )

        # ESI validation
        if payload.esi_number:
            esi = str(payload.esi_number).strip()

            if len(esi) > 17:
                raise HTTPException(
                    status_code=400,
                    detail="ESI number cannot exceed 17 characters"
                )

        # Email
        if payload.email:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.lower(Staff.email) == payload.email.lower()
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )

        # Phone
        if phone_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.phone_number == phone_number
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number already exists"
                )

        # PAN
        if pan_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.upper(Staff.pan_number) == pan_number
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="PAN number already exists"
                )

        # Aadhaar
        if payload.aadhar_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.aadhar_number == payload.aadhar_number
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number already exists"
                )

        # UAN
        if payload.uan_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.uan_number == payload.uan_number
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="UAN number already exists"
                )

        # ESI
        if payload.esi_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.esi_number == payload.esi_number
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="ESI number already exists"
                )

        staff = Staff(
            employee_id=next_code(self.db, PREFIX_STAFF),
            staff_code=next_code(self.db, PREFIX_STAFF),
            user_id=None,

            first_name=payload.first_name,
            last_name=payload.last_name,
            full_name=f"{payload.first_name} {payload.last_name or ''}".strip(),

            email=payload.email,
            phone_number=phone_number,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_number=payload.emergency_contact_number,

            gender=payload.gender,
            date_of_birth=payload.date_of_birth,

            address_street=payload.address_street,
            address_city=payload.address_city,
            address_state=payload.address_state,
            address_pincode=payload.address_pincode,
            address_country=payload.address_country,

            department=payload.department,
            designation=payload.designation,
            joining_date=payload.joining_date,
            role=payload.role,

            qualification=payload.qualification,
            experience_years=payload.experience_years,

            shift_type=payload.shift_type,
            shift_start=payload.shift_start,
            shift_end=payload.shift_end,

            monthly_salary=payload.monthly_salary,

            pan_number=payload.pan_number,
            aadhar_number=payload.aadhar_number,
            uan_number=payload.uan_number,
            esi_number=payload.esi_number,

            bank_account_holder_name=payload.bank_account_holder_name,
            bank_account_number=payload.bank_account_number,
            bank_ifsc_code=payload.bank_ifsc_code,
            bank_name=payload.bank_name,
            bank_branch_name=payload.bank_branch_name,
            bank_account_type=payload.bank_account_type,

            is_active=True,
        )

        if id_proof:
            staff.id_proof_url = upload_to_s3(id_proof, "staff/id_proofs")
            staff.id_proof_filename = id_proof.filename
            staff.id_proof_type = id_proof.content_type

        if address_proof:
            staff.address_proof_url = upload_to_s3(address_proof, "staff/address_proofs")
            staff.address_proof_filename = address_proof.filename
            staff.address_proof_type = address_proof.content_type

        if educational_certificates:
            staff.educational_certificates_urls = upload_to_s3(
                educational_certificates,
                "staff/educational_certificates"
            )
            staff.educational_certificates_filenames = educational_certificates.filename

        if experience_letters:
            staff.experience_letters_urls = upload_to_s3(
                experience_letters,
                "staff/experience_letters"
            )
            staff.experience_letters_filenames = experience_letters.filename

        if profile_photo:
            staff.profile_photo_url = upload_to_s3(profile_photo, "staff/profile_photos")
            staff.profile_photo_filename = profile_photo.filename

        if signature:
            staff.signature_url = upload_to_s3(signature, "staff/signatures")
            staff.signature_filename = signature.filename

        # tenant values
        self._apply_tenant(staff)

        self.db.add(staff)
        self.db.flush()

        # optional login user creation
        if payload.create_user:
            if not payload.password:
                raise HTTPException(
                    status_code=400,
                    detail="password is required when create_user=true"
                )

            _ensure_email_unique(self.db, payload.email)
            _ensure_phone_unique(self.db, payload.phone_number)

            user = User(
                email=payload.email,
                phone=_normalize_phone(payload.phone_number),
                password_hash=pwd.hash(payload.password),
                is_active=True,
                hospital_id=self.tenant.hospital_id,
                current_branch_id=self.tenant.branch_id,
            )

            self.db.add(user)
            self.db.flush()

            staff.user_id = user.id

            role_name = payload.role or "receptionist"

            role_ids = _role_ids(self.db, [role_name])
            role_id = role_ids[role_name]

            self.db.execute(
                text("INSERT INTO user_roles(user_id, role_id) VALUES (:u, :r)"),
                {
                    "u": user.id,
                    "r": role_id,
                },
            )

        self.db.commit()
        self.db.refresh(staff)

        return staff

    def update_staff(
            self,
            staff_id: int,
            payload: StaffUpdate,
            id_proof=None,
            address_proof=None,
            educational_certificates=None,
            experience_letters=None,
            profile_photo=None,
            signature=None,
    ):
        staff = self.db.query(Staff).filter(Staff.id == staff_id).first()

        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        # Phone validation
        if payload.phone_number:
            phone_number = _normalize_phone(payload.phone_number)

            if not (phone_number.isdigit() and len(phone_number) == 10):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number must contain exactly 10 digits"
                )

        # PAN validation
        if payload.pan_number:
            pan_number = _normalize_pan(payload.pan_number)

            if len(pan_number) > 10:
                raise HTTPException(
                    status_code=400,
                    detail="PAN number cannot exceed 10 characters"
                )

        # Aadhaar validation
        if payload.aadhar_number:
            aadhar = str(payload.aadhar_number).strip()

            if not (aadhar.isdigit() and len(aadhar) == 12):
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number must contain exactly 12 digits"
                )

        # UAN validation
        if payload.uan_number:
            uan = str(payload.uan_number).strip()

            if len(uan) > 12:
                raise HTTPException(
                    status_code=400,
                    detail="UAN number cannot exceed 12 digits"
                )

        # ESI validation
        if payload.esi_number:
            esi = str(payload.esi_number).strip()

            if len(esi) > 17:
                raise HTTPException(
                    status_code=400,
                    detail="ESI number cannot exceed 17 characters"
                )

        # Email duplicate
        if payload.email:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.lower(Staff.email) == payload.email.lower(),
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )

        # Phone duplicate
        if payload.phone_number:
            phone_number = _normalize_phone(payload.phone_number)

            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.phone_number == phone_number,
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Phone number already exists"
                )

        # PAN duplicate
        if payload.pan_number:
            pan_number = _normalize_pan(payload.pan_number)

            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                func.upper(Staff.pan_number) == pan_number,
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="PAN number already exists"
                )

        # Aadhaar duplicate
        if payload.aadhar_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.aadhar_number == payload.aadhar_number,
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Aadhaar number already exists"
                )

        # UAN duplicate
        if payload.uan_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.uan_number == payload.uan_number,
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="UAN number already exists"
                )

        # ESI duplicate
        if payload.esi_number:
            existing = self.db.query(Staff).filter(
                Staff.hospital_id == self.tenant.hospital_id,
                Staff.esi_number == payload.esi_number,
                Staff.id != staff.id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="ESI number already exists"
                )

        update_data = payload.model_dump(exclude_unset=True)

        password = update_data.pop("password", None)

        for key, value in update_data.items():
            if value is not None:
                setattr(staff, key, value)

        # Update login password
        if password and staff.user_id:
            user = self.db.get(User, staff.user_id)

            if user:
                user.password_hash = pwd.hash(password)

        if staff.first_name:
            staff.full_name = f"{staff.first_name} {staff.last_name or ''}".strip()

        if id_proof:
            staff.id_proof_url = upload_to_s3(id_proof, "staff_id_proofs")
            staff.id_proof_filename = id_proof.filename
            staff.id_proof_type = id_proof.content_type

        if address_proof:
            staff.address_proof_url = upload_to_s3(address_proof, "staff_address_proofs")
            staff.address_proof_filename = address_proof.filename
            staff.address_proof_type = address_proof.content_type

        if educational_certificates:
            staff.educational_certificates_urls = upload_to_s3(
                educational_certificates,
                "staff_educational_certificates"
            )
            staff.educational_certificates_filenames = educational_certificates.filename

        if experience_letters:
            staff.experience_letters_urls = upload_to_s3(
                experience_letters,
                "staff_experience_letters"
            )
            staff.experience_letters_filenames = experience_letters.filename

        if profile_photo:
            staff.profile_photo_url = upload_to_s3(profile_photo, "staff_profile_photos")
            staff.profile_photo_filename = profile_photo.filename

        if signature:
            staff.signature_url = upload_to_s3(signature, "staff_signatures")
            staff.signature_filename = signature.filename

        self.db.commit()
        self.db.refresh(staff)

        return staff

    def get_staff(self, staff_id: int):
        return self.db.query(Staff).filter(
            Staff.id == staff_id
        ).first()

    def get_all_staff(self):
        return self.db.query(Staff).all()

    def delete_staff(self, staff_id: int):
        staff = self.db.query(Staff).filter(
            Staff.id == staff_id
        ).first()

        if not staff:
            return {"message": "Staff not found"}

        self.db.delete(staff)
        self.db.commit()

        return {"message": "Staff deleted successfully"}

    def _ensure_staff_branch(self, staff_id, branch_id):
        existing = self.db.execute(
            select(StaffBranch).where(
                StaffBranch.staff_id == staff_id,
                StaffBranch.branch_id == branch_id
            )
        ).scalar_one_or_none()

        if not existing:
            sb = StaffBranch(
                staff_id=staff_id,
                branch_id=branch_id
            )
            self.db.add(sb)
            self.db.flush()

    # ================= Users / Roles (raw) =================

    def create_user(self, payload):
        if not payload.roles:
            raise _bad("roles cannot be empty")
        if "doctor" in payload.roles:
            # it's OK technically, but steer callers to /admin/doctors flow for proper linking
            raise _bad("Use /admin/doctors to create users with 'doctor' role")

        _ensure_email_unique(self.db, payload.email)
        _ensure_phone_unique(self.db, payload.phone)

        u = User(
            username=payload.email.split("@")[0],
            email=payload.email,
            phone=_normalize_phone(payload.phone),
            password_hash=pwd.hash(payload.password),
            role=payload.roles[0],
            is_active=True,
            hospital_id=self.tenant.hospital_id,
            current_branch_id=self.tenant.branch_id,
        )
        self.db.add(u)
        self.db.flush()

        rids = _role_ids(self.db, payload.roles)
        for rid in rids.values():
            self.db.execute(text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
                            {"u": u.id, "r": rid})

        self.db.commit()
        return {"id": u.id, "email": u.email, "is_active": u.is_active, "roles": sorted(list(rids.keys()))}

    def get_users(self):
        users = (
            self.db.query(User)
            .filter(
                User.hospital_id == self.tenant.hospital_id
            )
            .all()
        )

        result = []

        for u in users:
            result.append({
                "id": u.id,
                "email": u.email,
                "phone": u.phone,
                "is_active": u.is_active,
                "roles": [r.name for r in u.roles]
            })

        return result

    def get_user(self, user_id: int):

        user = (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.hospital_id == self.tenant.hospital_id
            )
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "roles": [r.name for r in user.roles]
        }

    # def update_user(self, user_id: int, payload: UserCreateIn):
    #
    #     user = self.db.get(User, user_id)
    #
    #     if not user:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="User not found"
    #         )
    #
    #     for key, value in payload.model_dump(exclude_unset=True).items():
    #         setattr(user, key, value)
    #
    #     self.db.commit()
    #     self.db.refresh(user)
    #
    #     return user

    def update_user(self, user_id: int, payload: UserCreateIn):

        user = self.db.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        data = payload.model_dump(exclude_unset=True)

        roles_data = data.pop("roles", None)

        # Handle password separately
        password = data.pop("password", None)

        if password:
            user.password_hash = pwd.hash(password)

        # Update other fields
        if "email" in data:
            user.email = data["email"]

        if "phone" in data:
            user.phone = _normalize_phone(data["phone"])

        if "is_active" in data:
            user.is_active = data["is_active"]

        if "current_branch_id" in data:
            user.current_branch_id = data["current_branch_id"]

        # Handle roles
        if roles_data is not None:
            role_objs = (
                self.db.query(Role)
                .filter(Role.name.in_(roles_data))
                .all()
            )
            user.roles = role_objs

        self.db.commit()
        self.db.refresh(user)

        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "roles": [role.name for role in user.roles]
        }

    def delete_user(self, user_id: int):

        user = self.db.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        self.db.delete(user)
        self.db.commit()

    def set_user_roles(self, user_id: int, roles: list[str]):
        if not self.db.get(User, user_id):
            raise _bad("User not found", 404)
        rids = _role_ids(self.db, roles)
        self.db.execute(text("DELETE FROM user_roles WHERE user_id=:u"), {"u": user_id})
        for rid in rids.values():
            self.db.execute(text("INSERT INTO user_roles(user_id, role_id) VALUES (:u,:r)"),
                            {"u": user_id, "r": rid})
        self.db.commit()
        return {"user_id": user_id, "roles": sorted(list(rids.keys()))}


