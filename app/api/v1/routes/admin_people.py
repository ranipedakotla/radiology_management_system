from sqlalchemy.orm import Session

from app.models.org import Hospital, Branch, Department
from app.schemas.admin_people import StaffResponse, StaffUpdate
from app.core.security import require_roles, get_db
from app.schemas.org import DepartmentCreate
from app.utils.tenant import Tenant, get_tenant

from app.schemas.admin_people import (
    PatientCreateIn, PatientOut,
    DoctorCreateIn, DoctorOut,StaffCreateIn,
 StaffOut,
    UserCreateIn, UserOut,
)
from app.services.admin_people import AdminPeopleService, StaffService
from app.utils.s3 import upload_to_s3
from app.schemas.admin_people import Gender, BloodGroup, MaritalStatus
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_db
from typing import Annotated, Optional
from fastapi import Form, File, UploadFile, Depends, HTTPException
from pydantic import EmailStr
from datetime import date
from app.models.people import GenderEnum, ShiftTypeEnum, AccountTypeEnum

router = APIRouter(prefix="/admin", tags=["Admin: People"])

# Patients
# @router.post("/patients", response_model=PatientOut,
#              dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))])
# def create_patient(payload: PatientCreateIn,
#                    tenant: Tenant = Depends(get_tenant),
#                    db: Session = Depends(get_db)):
#     return AdminPeopleService(db, tenant).create_patient(payload)

@router.post(
    "/patients",
    response_model=PatientOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin","receptionist"))],
)
async def create_patient(
    # existing
    first_name: str = Form(...),
    last_name: str  = Form(...),
    dob: date | str = Form(...),
    phone: str = Form(...),

    # NEW fields (all optional for now)
    guardian_name: str = Form(...),
    gender: Gender | str = Form(...),
    age: int = Form(...),
    blood_group: BloodGroup  = Form(...),
    marital_status: MaritalStatus = Form(...),
    email: str  = Form(...),
    location: str  = Form(...),
    reason: str  = Form(...),
    aadhaar_no: str  = Form(...),

    # file
    # aadhaar_card: UploadFile | None = File(None),
    aadhaar_card: UploadFile = Form(...),

        tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    # Save file to /static for now
    aadhaar_path = ""
    if aadhaar_card:
        aadhaar_path = upload_to_s3(aadhaar_card, folder="aadhaar")

    payload = PatientCreateIn(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone_number=phone,
        guardian_name=guardian_name,
        gender=gender,
        age=age,
        blood_group=blood_group,
        marital_status=marital_status,
        email=email,
        location=location,
        reason=reason,
        aadhaar_no=aadhaar_no,
    )

    return AdminPeopleService(db, tenant).create_patient(payload, aadhaar_file_path=aadhaar_path)


@router.put(
    "/patients/{patient_id}",
    response_model=PatientOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
async def update_patient(
        patient_id: int,

        # existing
        first_name: str = Form(...),
        last_name: str = Form(...),
        dob: date  = Form(...),
        phone: str = Form(...),

        # extra fields
        guardian_name: str = Form(...),
        gender: Gender = Form(...),
        age: int = Form(...),
        blood_group: BloodGroup = Form(...),
        marital_status: MaritalStatus = Form(...),
        email: str = Form(...),
        location: str = Form(...),
        reason: str = Form(...),
        aadhaar_no: str = Form(...),

        # file
        aadhaar_card: UploadFile | None = File(None),

        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    aadhaar_path = None

    if aadhaar_card:
        aadhaar_path = upload_to_s3(
            upload=aadhaar_card,
            folder="aadhaar"
        )

    payload = PatientCreateIn(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone_number=phone,
        guardian_name=guardian_name,
        gender=gender,
        age=age,
        blood_group=blood_group,
        marital_status=marital_status,
        email=email,
        location=location,
        reason=reason,
        aadhaar_no=aadhaar_no,
    )

    return AdminPeopleService(
        db,
        tenant
    ).update_patient(
        patient_id=patient_id,
        payload=payload,
        aadhaar_file_path=aadhaar_path
    )

@router.delete(
    "/patients/{patient_id}",
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
async def delete_patient(
        patient_id: int,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    AdminPeopleService(
        db,
        tenant
    ).delete_patient(patient_id)

    return {
        "message": "Patient deleted successfully"
    }

@router.post("/", dependencies=[Depends(require_roles("admin", "superadmin"))])
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    hospital = db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    branch = db.query(Branch).filter(
        Branch.id == payload.branch_id,
        Branch.hospital_id == payload.hospital_id
    ).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found for this hospital")

    existing = db.query(Department).filter(
        Department.name == payload.name,
        Department.branch_id == payload.branch_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists in this branch")

    department = Department(
        name=payload.name,
        hospital_id=payload.hospital_id,
        branch_id=payload.branch_id
    )
    db.add(department)
    db.commit()
    db.refresh(department)

    return {
        "success": True,
        "message": "Department created successfully",
        "data": {
            "id": department.id,
            "name": department.name,
            "hospital_id": department.hospital_id,
            "hospital_name": department.hospital.name,
            "branch_id": department.branch_id,
            "branch_name": department.branch.name,
        }
    }

@router.get("/list", dependencies=[Depends(require_roles("admin", "superadmin"))])
def get_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()

    return {
        "success": True,
        "count": len(departments),
        "data": [
            {
                "id": d.id,
                "name": d.name,
                "hospital_id": d.hospital_id,
                "hospital_name": d.hospital.name,
                "branch_id": d.branch_id,
                "branch_name": d.branch.name,
            }
            for d in departments
        ]
    }


@router.post(
    "/doctors",
    response_model=DoctorOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def create_doctor(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(...),
    consultation_fee: int = Form(0),
    specialty: Optional[str] = Form(...),
    doctor_code: Optional[str] = Form(...),
    designation: Optional[str] = Form(...),
    department: str = Form(...),
    specialization: Optional[str] = Form(...),
    experience: Optional[int] = Form(0),


    # Staff required fields
    email: EmailStr = Form(...),
    phone: str = Form(...),
    gender: GenderEnum = Form(...),
    date_of_birth: date = Form(...),
    emergency_contact_name: str = Form(...),
    emergency_contact_number: str = Form(...),
    address_city: str = Form(...),
    address_state: str = Form(...),
    address_pincode: str = Form(...),
    joining_date: date = Form(...),
    qualification: str = Form(...),
    monthly_salary: float = Form(...),
    shift_type: ShiftTypeEnum = Form(...),
    shift_start: Optional[str] = Form(...),
    shift_end: Optional[str] = Form(...),
    pan_number: str = Form(...),
    aadhar_number: str = Form(...),
    bank_account_holder_name: str = Form(...),
    bank_account_number: str = Form(...),
    bank_ifsc_code: str = Form(...),
    bank_name: str = Form(...),
    uan_number: Optional[int] = Form(None),
    esi_number: Optional[str] = Form(None),
    floor_location: Optional[str] = Form(None),
    # bank_name: str = Form(...),

    # Optional files
    profile_pic: Annotated[UploadFile | None, File()] = None,
    signature: Annotated[UploadFile | None, File()] = None,
    license_file: Annotated[UploadFile | None, File()] = None,

    create_user: bool = Form(False),
    password: Optional[str] = Form(None),

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    payload = DoctorCreateIn(
        first_name=first_name,
        last_name=last_name,
        consultation_fee=consultation_fee,
        specialty=specialty,
        doctor_code=doctor_code,
        designation=designation,
        specialization=specialization,
        experience=experience,
        department=department,
        uan_number=uan_number,
        esi_number=esi_number,
        floor_location=floor_location,

        email=email,
        phone=phone,
        gender=gender,
        date_of_birth=date_of_birth,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_number=emergency_contact_number,
        address_city=address_city,
        address_state=address_state,
        address_pincode=address_pincode,
        joining_date=joining_date,
        qualification=qualification,
        monthly_salary=monthly_salary,
        shift_type=shift_type,
        shift_start=shift_start,
        shift_end=shift_end,
        pan_number=pan_number,
        aadhar_number=aadhar_number,
        bank_account_holder_name=bank_account_holder_name,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,
        bank_name=bank_name,
        create_user=create_user,
        password=password,
    )
    profile_pic_url = None
    signature_url = None
    license_file_url = None

    if profile_pic:
        profile_pic_url = upload_to_s3(
            upload=profile_pic,
            folder="doctor/profile_pic"
        )

    if signature:
        signature_url = upload_to_s3(
            upload=signature,
            folder="doctor/signature"
        )

    if license_file:
        license_file_url = upload_to_s3(
            upload=license_file,
            folder="doctor/license"
        )


    return AdminPeopleService(db, tenant).create_doctor(
        payload,
        profile_pic_url=profile_pic_url,
        signature_url=signature_url,
        license_file_url=license_file_url,
    )



@router.put(
    "/doctors/{doctor_id}",
    response_model=DoctorOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def update_doctor(
    doctor_id: int,

    # Doctor + Staff basic
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),

    consultation_fee: Optional[int] = Form(None),
    specialty: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    experience: Optional[int] = Form(0),


    # Staff fields
    email: Optional[EmailStr] = Form(None),
    phone: Optional[str] = Form(None),
    gender: Optional[GenderEnum] = Form(None),
    date_of_birth: Optional[date] = Form(None),

    emergency_contact_name: Optional[str] = Form(None),
    emergency_contact_number: Optional[str] = Form(None),

    address_city: Optional[str] = Form(None),
    address_state: Optional[str] = Form(None),
    address_pincode: Optional[str] = Form(None),

    joining_date: Optional[date] = Form(None),
    qualification: Optional[str] = Form(None),
    monthly_salary: Optional[float] = Form(None),
    shift_type: Optional[ShiftTypeEnum] = Form(None),

    pan_number: Optional[str] = Form(None),
    aadhar_number: Optional[str] = Form(None),
    uan_number: Optional[int] = Form(None),
    esi_number: Optional[str] = Form(None),
    floor_location: Optional[str] = Form(None),

    bank_account_holder_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    bank_ifsc_code: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    password: Optional[str] = Form(None),

    # File uploads
    profile_pic: Annotated[UploadFile | None, File()] = None,
    signature: Annotated[UploadFile | None, File()] = None,
    license_file: Annotated[UploadFile | None, File()] = None,

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    service = AdminPeopleService(db, tenant)

    print(")))))))))))))))))",uan_number, type(uan_number))
    print(")))))))))))))))))",esi_number,type(esi_number))

    profile_pic_url = None
    signature_url = None
    license_file_url = None

    if profile_pic:
        profile_pic_url = upload_to_s3(
            upload=profile_pic,
            folder="doctor/profile_pic"
        )

    if signature:
        signature_url = upload_to_s3(
            upload=signature,
            folder="doctor/signature"
        )

    if license_file:
        license_file_url = upload_to_s3(
            upload=license_file,
            folder="doctor/license"
        )

    updated = service.update_doctor(
        doctor_id=doctor_id,
        first_name=first_name,
        last_name=last_name,
        consultation_fee=consultation_fee,
        specialty=specialty,
        designation=designation,
        department=department,
        specialization=specialization,
        experience=experience,
        email=email,
        phone=phone,
        gender=gender,
        date_of_birth=date_of_birth,
        uan_number=uan_number,
        esi_number=esi_number,
        floor_location=floor_location,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_number=emergency_contact_number,

        address_city=address_city,
        address_state=address_state,
        address_pincode=address_pincode,

        joining_date=joining_date,
        qualification=qualification,
        monthly_salary=monthly_salary,
        shift_type=shift_type,

        pan_number=pan_number,
        aadhar_number=aadhar_number,
        password=password,

        bank_account_holder_name=bank_account_holder_name,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,
        bank_name=bank_name,

        profile_pic=profile_pic_url,
        signature=signature_url,
        license_file=license_file_url,
    )

    return updated


@router.delete(
    "/doctors/{doctor_id}",
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def delete_doctor(
    doctor_id: int,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    service = AdminPeopleService(db, tenant)

    doctor = service.get_doctor_by_id(doctor_id)

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    service.delete_doctor(doctor_id)

    return {"message": "Doctor deleted successfully"}



@router.post("/staff", response_model=StaffResponse)
def create_staff(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(None),

    email: EmailStr = Form(...),
    phone_number: str = Form(...),
    gender: GenderEnum = Form(...),
    date_of_birth: date = Form(...),
    emergency_contact_name: str = Form(...),
    emergency_contact_number: str = Form(...),

    address_street: Optional[str] = Form(None),
    address_city: str = Form(...),
    address_state: str = Form(...),
    address_pincode: str = Form(...),
    address_country: str = Form("India"),

    department: str = Form(...),
    designation: str = Form(...),
    joining_date: date = Form(...),
    role: str = Form("EMPLOYEE"),

    qualification: str = Form(...),
    experience_years: float = Form(0.0),

    shift_type: ShiftTypeEnum = Form(ShiftTypeEnum.FLEXIBLE),
    shift_start: Optional[str] = Form(None),
    shift_end: Optional[str] = Form(None),

    monthly_salary: float = Form(...),

    pan_number: str = Form(...),
    aadhar_number: str = Form(...),
    uan_number: Optional[str] = Form(None),
    esi_number: Optional[str] = Form(None),

    bank_account_holder_name: str = Form(...),
    bank_account_number: str = Form(...),
    bank_ifsc_code: str = Form(...),
    bank_name: str = Form(...),
    bank_branch_name: Optional[str] = Form(None),
    bank_account_type: AccountTypeEnum = Form(AccountTypeEnum.SAVINGS),

    id_proof: Annotated[UploadFile | None, File()] = None,
    address_proof: Annotated[UploadFile | None, File()] = None,
    educational_certificates: Annotated[UploadFile | None, File()] = None,
    experience_letters: Annotated[UploadFile | None, File()] = None,
    profile_photo: Annotated[UploadFile | None, File()] = None,
    signature: Annotated[UploadFile | None, File()] = None,
    create_user: bool = Form(False),
    password: Optional[str] = Form(None),
    tenant: Tenant = Depends(get_tenant),


    db: Session = Depends(get_db),

):
    payload = StaffCreateIn(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_number=phone_number,
        gender=gender,
        date_of_birth=date_of_birth,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_number=emergency_contact_number,
        address_street=address_street,
        address_city=address_city,
        address_state=address_state,
        address_pincode=address_pincode,
        address_country=address_country,
        department=department,
        designation=designation,
        joining_date=joining_date,
        role=role,
        qualification=qualification,
        experience_years=experience_years,
        shift_type=shift_type,
        shift_start=shift_start,
        shift_end=shift_end,
        monthly_salary=monthly_salary,
        pan_number=pan_number,
        aadhar_number=aadhar_number,
        uan_number=uan_number,
        esi_number=esi_number,
        bank_account_holder_name=bank_account_holder_name,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,
        bank_name=bank_name,
        bank_branch_name=bank_branch_name,
        bank_account_type=bank_account_type,
        create_user=create_user,
        password=password,
    )

    return StaffService(db,tenant).create_staff(
        payload,
        id_proof=id_proof,
        address_proof=address_proof,
        educational_certificates=educational_certificates,
        experience_letters=experience_letters,
        profile_photo=profile_photo,
        signature=signature,
    )

@router.put("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: int,

    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    full_name: Optional[str] = Form(None),

    email: Optional[EmailStr] = Form(None),
    phone_number: Optional[str] = Form(None),
    gender: Optional[GenderEnum] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    emergency_contact_name: Optional[str] = Form(None),
    emergency_contact_number: Optional[str] = Form(None),

    address_street: Optional[str] = Form(None),
    address_city: Optional[str] = Form(None),
    address_state: Optional[str] = Form(None),
    address_pincode: Optional[str] = Form(None),
    address_country: Optional[str] = Form(None),

    department: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),

    joining_date: Optional[date] = Form(None),
    role: Optional[str] = Form(None),

    qualification: Optional[str] = Form(None),
    experience_years: Optional[float] = Form(None),

    shift_type: Optional[ShiftTypeEnum] = Form(None),
    shift_start: Optional[str] = Form(None),
    shift_end: Optional[str] = Form(None),

    monthly_salary: Optional[float] = Form(None),

    pan_number: Optional[str] = Form(None),
    aadhar_number: Optional[str] = Form(None),
    uan_number: Optional[str] = Form(None),
    esi_number: Optional[str] = Form(None),
    password: Optional[str] = Form(None),

    bank_account_holder_name: Optional[str] = Form(None),
    bank_account_number: Optional[str] = Form(None),
    bank_ifsc_code: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    bank_branch_name: Optional[str] = Form(None),
    bank_account_type: Optional[AccountTypeEnum] = Form(None),

    id_proof: Annotated[UploadFile | None, File()] = None,
    address_proof: Annotated[UploadFile | None, File()] = None,
    educational_certificates: Annotated[UploadFile | None, File()] = None,
    experience_letters: Annotated[UploadFile | None, File()] = None,
    profile_photo: Annotated[UploadFile | None, File()] = None,
    signature: Annotated[UploadFile | None, File()] = None,

    db: Session = Depends(get_db),
tenant: Tenant = Depends(get_tenant),
):
    payload = StaffUpdate(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        email=email,
        phone_number=phone_number,
        gender=gender,
        date_of_birth=date_of_birth,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_number=emergency_contact_number,
        address_street=address_street,
        address_city=address_city,
        address_state=address_state,
        address_pincode=address_pincode,
        address_country=address_country,
        department=department,
        designation=designation,
        joining_date=joining_date,
        role=role,
        qualification=qualification,
        experience_years=experience_years,
        shift_type=shift_type,
        shift_start=shift_start,
        shift_end=shift_end,
        monthly_salary=monthly_salary,
        pan_number=pan_number,
        aadhar_number=aadhar_number,
        uan_number=uan_number,
        esi_number=esi_number,
        bank_account_holder_name=bank_account_holder_name,
        bank_account_number=bank_account_number,
        bank_ifsc_code=bank_ifsc_code,
        bank_name=bank_name,
        bank_branch_name=bank_branch_name,
        bank_account_type=bank_account_type,
        password=password,
    )

    return StaffService(db, tenant).update_staff(
        staff_id,
        payload,
        id_proof=id_proof,
        address_proof=address_proof,
        educational_certificates=educational_certificates,
        experience_letters=experience_letters,
        profile_photo=profile_photo,
        signature=signature,
    )

@router.get("/{staff_id}", response_model=StaffResponse)
def get_staff(staff_id: int,tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    staff = StaffService(db,tenant).get_staff(staff_id)

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    return staff


@router.get("/", response_model=list[StaffResponse])
def get_all_staff(tenant: Tenant = Depends(get_tenant),db: Session = Depends(get_db)):
    return StaffService(db,tenant).get_all_staff()


@router.delete("/{staff_id}")
def delete_staff(staff_id: int,tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return StaffService(db,tenant).delete_staff(staff_id)

# Users (raw) + roles
@router.post("/users", response_model=UserOut
             # dependencies=[Depends(require_roles(""))]
             )
def create_user(payload: UserCreateIn,
                tenant: Tenant = Depends(get_tenant),
                db: Session = Depends(get_db)):
    return StaffService(db, tenant).create_user(payload)

@router.post("/users/{user_id}/roles",
             dependencies=[Depends(require_roles("superadmin"))])
def set_user_roles(user_id: int, roles: list[str],
                   tenant: Tenant = Depends(get_tenant),
                   db: Session = Depends(get_db)):
    return StaffService(db, tenant).set_user_roles(user_id, roles)

@router.get(
    "/all/users",
    response_model=list[UserOut],
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def get_users(
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    return StaffService(db, tenant).get_users()


@router.get(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def get_user(
    user_id: int,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    return StaffService(db, tenant).get_user(user_id)


@router.put(
    "/users/{user_id}",
    response_model=UserOut,
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def update_user(
        user_id: int,
        payload: UserCreateIn,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    return StaffService(
        db,
        tenant
    ).update_user(user_id, payload)


@router.delete(
    "/users/{user_id}",
    dependencies=[Depends(require_roles("branch_admin", "admin", "superadmin"))],
)
def delete_user(
        user_id: int,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    StaffService(
        db,
        tenant
    ).delete_user(user_id)
    return {
        "message": "User deleted successfully"
    }