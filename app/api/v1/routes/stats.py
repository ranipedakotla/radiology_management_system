from fastapi import APIRouter, Depends,HTTPException,Query
from sqlalchemy import select, or_, func, distinct
from sqlalchemy.orm import Session
from datetime import date,datetime
from app.schemas.admin_people import DoctorOut, PatientOut
from app.core.security import require_roles, get_db
from sqlalchemy import cast,String
from app.utils.tenant import Tenant, get_tenant
from app.models.people import Doctor, Patient, Staff,DoctorBranch, PatientBranchCode
from app.schemas.stats import (
    DoctorCountOut,
    PatientCountOut,
    DoctorLiteOut,
    PatientLiteOut,
)
from sqlalchemy import select, or_, func

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get(
    "/doctor-count",
    response_model=DoctorCountOut,
    dependencies=[Depends(require_roles(
        "receptionist",
        "doctor",
        "nurse",
        "accountant",
        "admin",
        "superadmin"
    ))]
)
def doctor_count(
        doctor_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,

        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    stmt = (
        select(func.count(distinct(Doctor.id)))
        .join(DoctorBranch, DoctorBranch.doctor_id == Doctor.id)
        .where(
            Doctor.hospital_id == tenant.hospital_id,
            DoctorBranch.branch_id == tenant.branch_id,
        )
    )

    # Filter by doctor ID
    if doctor_id:
        stmt = stmt.where(Doctor.id == doctor_id)

    # From date
    if from_date:
        stmt = stmt.where(func.date(Doctor.created_at) >= from_date)

    # To date
    if to_date:
        stmt = stmt.where(func.date(Doctor.created_at) <= to_date)

    total = db.execute(stmt).scalar() or 0

    return {
        "total_doctors": int(total)
    }


@router.get(
    "/patient-count",
    response_model=PatientCountOut,
    dependencies=[Depends(require_roles(
        "receptionist",
        "doctor",
        "nurse",
        "accountant",
        "admin",
        "superadmin"
    ))]
)
def patient_count(
        patient_id: int | None = Query(None),
        from_date: date | None = Query(None),
        to_date: date | None = Query(None),
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db)
):
    stmt = (
        select(func.count(distinct(Patient.id)))
        .join(PatientBranchCode, PatientBranchCode.patient_id == Patient.id)
        .where(
            Patient.hospital_id == tenant.hospital_id,
            PatientBranchCode.branch_id == tenant.branch_id,
        )
    )

    # Filter by patient_id
    if patient_id:
        stmt = stmt.where(Patient.id == patient_id)

    # Filter by from_date
    if from_date:
        stmt = stmt.where(func.date(Patient.created_at) >= from_date)

    # Filter by to_date
    if to_date:
        stmt = stmt.where(func.date(Patient.created_at) <= to_date)

    total = db.execute(stmt).scalar() or 0

    return {
        "total_patients": int(total)
    }




@router.get(
    "/doctors",
    response_model=list[DoctorLiteOut],
    dependencies=[Depends(require_roles("receptionist", "doctor", "nurse", "accountant", "admin", "superadmin"))],
)
def doctor_list(
    # q: str | None = None,
    # specialty: str | None = None,
    doctor_id:int |None=None,
    doctor_name:str|None=None,
    limit: int = 100,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            Doctor.id.label("id"),

            Doctor.doctor_code.label("doctor_code"),

            Staff.first_name.label("fn"),
            Staff.last_name.label("ln"),

            Doctor.consultation_fee.label("fee"),
            Doctor.specialty.label("specialty"),
        )
        .join(DoctorBranch, DoctorBranch.doctor_id == Doctor.id)
        .join(Staff, Staff.id == Doctor.staff_id)
        .where(
            Doctor.hospital_id == tenant.hospital_id,
            DoctorBranch.branch_id == tenant.branch_id,
        )
    )

    if doctor_id:
        like = f"%{doctor_id}%"

        stmt = stmt.where(
            or_(
                cast(Doctor.id, String).ilike(like),
                Doctor.doctor_code.ilike(like),
            )
        )
    # Search by doctor name
    if doctor_name:
        like = f"%{doctor_name}%"

        stmt = stmt.where(
            or_(
                Staff.first_name.ilike(like),
                Staff.last_name.ilike(like),

                func.concat(
                    Staff.first_name,
                    " ",
                    func.coalesce(Staff.last_name, "")
                ).ilike(like),
            )
        )

    stmt = (
        stmt
        .order_by(Staff.first_name.asc(), Staff.last_name.asc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    return [
        {
            "id": r.id,
            "doctor_code": r.doctor_code,
            "name": f"{r.fn} {r.ln}".strip(),
            "consultation_fee": r.fee,
            "specialty": r.specialty,
        }
        for r in rows
    ]



@router.get(
    "/doctors/{doctor_id}",
    response_model=DoctorOut,
    dependencies=[Depends(require_roles(
        "receptionist",
        "doctor",
        "nurse",
        "accountant",
        "admin",
        "superadmin"
    ))]
)
def get_doctor(
        doctor_id: int,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    stmt = (
        select(
            Doctor.id.label("doctor_id"),
            Doctor.doctor_code,

            Staff.first_name,
            Staff.last_name,

            Staff.id.label("staff_id"),
            Staff.staff_code,

            Doctor.consultation_fee,
            Doctor.specialty,
            Doctor.designation,
            Doctor.department,
            Doctor.specialization,

            Doctor.signature_url,
            Doctor.license_url,
            Doctor.profile_pic_url,


            Doctor.pan,
            Doctor.aadhar,

            Doctor.bank,
            Doctor.account_no,
            Doctor.ifsc,

            Doctor.floor_location,
            Doctor.shift_start,
            Doctor.shift_end,
            Staff.uan_number,
            Staff.esi_number,
            Staff.user_id,
            Staff.qualification,
            Staff.gender,
            Staff.email,
            Staff.phone_number,
            Staff.date_of_birth,
            Staff.address_city,
            Staff.address_state,
            Staff.address_country,
            Staff.address_street,
            Staff.address_pincode,
            Staff.experience_years
        )
        .join(Staff, Staff.id == Doctor.staff_id)
        .join(DoctorBranch, DoctorBranch.doctor_id == Doctor.id)
        .where(
            Doctor.id == doctor_id,
            Doctor.hospital_id == tenant.hospital_id,
            DoctorBranch.branch_id == tenant.branch_id,
        )
    )

    row = db.execute(stmt).first()
    print("00000000000000000000",row)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    return {
        "id": row.doctor_id,
        "qualification": row.qualification,
        "gender": row.gender,
        "email": row.email,
        "phone_number": row.phone_number,
        "doctor_code": row.doctor_code,

        "first_name": row.first_name,
        "last_name": row.last_name,

        "staff_id": row.staff_id,
        "staff_code": row.staff_code,

        "user_id": row.user_id,

        "consultation_fee": row.consultation_fee,
        "specialty": row.specialty,

        "designation": row.designation,
        "department": row.department,
        "specialization": row.specialization,
        "shift_start": row.shift_start,
        "shift_end": row.shift_end,

        "signature_url": row.signature_url,
        "license_url": row.license_url,
        "profile_pic_url": row.profile_pic_url,

        "uan_number": row.uan_number,
        "esi_number": row.esi_number,
        "pan": row.pan,
        "aadhar": row.aadhar,

        "bank": row.bank,
        "account_no": row.account_no,
        "ifsc": row.ifsc,

        "floor_location": row.floor_location,
        "date_of_birth": row.date_of_birth,
        "address_city": row.address_city,
        "address_state": row.address_state,
        "address_country": row.address_country,
        "address_pincode": row.address_pincode,
        "address_street": row.address_street,
        "experience": row.experience_years,
    }


@router.get(
    "/patients",
    response_model=list[PatientLiteOut],
    dependencies=[Depends(require_roles(
        "receptionist", "doctor", "nurse",
        "accountant", "admin", "superadmin"
    ))]
)
def patient_list(
    q: str | None = None,
    limit: int = 100,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db)
):

    stmt = (
        select(
            Patient.id.label("id"),
            Patient.first_name.label("fn"),
            Patient.last_name.label("ln"),
            Patient.phone_number.label("phone_number"),   # added
            Patient.gender.label("gender"),   # added
            Patient.dob.label("dob"),   # added
        )
        .join(PatientBranchCode, PatientBranchCode.patient_id == Patient.id)
        .where(
            Patient.hospital_id == tenant.hospital_id,
            PatientBranchCode.branch_id == tenant.branch_id,
        )
        .order_by(Patient.first_name.asc(), Patient.last_name.asc())
        .limit(limit)
    )

    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.phone_number.ilike(like),   # optional search by phone
            )
        )

    rows = db.execute(stmt).all()
    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>",rows)

    return [
        {
            "id": r.id,
            "phone_number": r.phone_number,
            "name": f"{r.fn} {r.ln}".strip(),
            "gender":r.gender,
            "dob":r.dob
        }
        for r in rows
    ]

@router.get(
    "/patients/{patient_id}",
    response_model=PatientOut,
    dependencies=[Depends(require_roles(
        "receptionist",
        "doctor",
        "nurse",
        "accountant",
        "admin",
        "superadmin"
    ))]
)
def get_patient(
    patient_id: int,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            Patient.id.label("patient_id"),

            Patient.patient_uid,
            Patient.patient_code,

            Patient.first_name,
            Patient.last_name,

            Patient.phone_number,
            Patient.dob,

            Patient.guardian_name,
            Patient.gender,
            Patient.age,
            Patient.blood_group,
            Patient.marital_status,

            Patient.email,
            Patient.location,
            Patient.reason,

            Patient.aadhaar_no,
            Patient.aadhaar_file_path,

            Patient.created_at,
        )
        .join(
            PatientBranchCode,
            PatientBranchCode.patient_id == Patient.id
        )
        .where(
            Patient.id == patient_id,
            Patient.hospital_id == tenant.hospital_id,
            PatientBranchCode.branch_id == tenant.branch_id,
        )
    )

    row = db.execute(stmt).first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return {
        "id": row.patient_id,

        "patient_uid": row.patient_uid,
        "patient_code": row.patient_code,

        "first_name": row.first_name,
        "last_name": row.last_name,

        "phone_number": row.phone_number,
        "dob": row.dob,

        "guardian_name": row.guardian_name,
        "gender": row.gender,
        "age": row.age,
        "blood_group": row.blood_group,
        "marital_status": row.marital_status,

        "email": row.email,
        "location": row.location,
        "reason": row.reason,

        "aadhaar_no": row.aadhaar_no,
        "aadhaar_file_path": row.aadhaar_file_path,

        "created_at": row.created_at,
    }