import os
import uuid
from typing import Optional, Union

import boto3
import pandas as pd

from app.core.settings import settings
from app.models.schedule import DoctorSchedule
from app.services.appointments import AppointmentService
from app.utils.s3 import upload_to_s3
from app.utils.tenant import Tenant, get_tenant
from app.models.appointments import PriorityEnum
from fastapi import UploadFile, File, HTTPException
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.core.security import require_roles, get_db
from app.schemas.appointments import (
    AppointmentCreate, AppointmentOutIDs, AppointmentListOut,
    AppointmentDetailOut, AppointmentCancelIn,
    AvailabilitySlotOut,
)
from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException

from app.models.people import Patient
from app.models.appointments import Appointment
from sqlalchemy import select, func
router = APIRouter(prefix="/appointments", tags=["Appointments"])


s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

@router.get("/availability", response_model=list[AvailabilitySlotOut],
            dependencies=[Depends(require_roles("receptionist","front_office","admin","superadmin","doctor"))])
def availability(doctor_id: int, for_date: str,
                 tenant: Tenant = Depends(get_tenant),
                 db: Session = Depends(get_db)):
    d = date.fromisoformat(for_date)
    service = AppointmentService(db, tenant)
    if doctor_id:
        return service.availability(doctor_id, d)

    else:
        return service.availability_all_doctors(d)
    return AppointmentService(db, tenant).availability(doctor_id, d)

# @router.get("/availability")
# def availability(
#     for_date: str,
#     doctor_id: int,
#     tenant: Tenant = Depends(get_tenant),
#     db = Depends(get_db)
# ):
#     from datetime import date
#
#     d = date.fromisoformat(for_date)
#     service = AppointmentService(db, tenant)
#
#     if doctor_id:
#         return service.availability(doctor_id, d)
#     else:
#         return service.availability_all_doctors(d)

@router.post("/availability")
def create_availability(
    doctor_id: int,
    date_value: str,
    start_time: str,
    end_time: str,
    hospital_id: int,
    branch_id: int,
    slot_minutes: int = 15,
    max_patients: int = 0,
    db: Session = Depends(get_db),
):
    # Convert date
    try:
        date_obj = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    # Convert time
    try:
        start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()
    except ValueError:
        raise HTTPException(400, "Invalid time format. Use HH:MM:SS")

    # Validate time
    if start_time_obj >= end_time_obj:
        raise HTTPException(400, "start_time must be before end_time")

        # add new
    now = datetime.now()
    # Prevent past date
    if date_obj < now.date():
        raise HTTPException(
                status_code=400,
                detail="Cannot create availability for a past date."
        )
    # Prevent past time if schedule is for today
    schedule_start = datetime.combine(date_obj, start_time_obj)
    if schedule_start < now:
        raise HTTPException(
                status_code=400,
                detail="Cannot create availability for a past time."
        )
        # end

    # Check duplicate
    stmt = select(DoctorSchedule).where(
        DoctorSchedule.doctor_id == doctor_id,
        DoctorSchedule.schedule_date == date_obj,  # <-- is this 2026-06-26?
        DoctorSchedule.start_time == start_time_obj,  # <-- is this 03:00:00?
        DoctorSchedule.end_time == end_time_obj,
        DoctorSchedule.hospital_id == hospital_id,
        DoctorSchedule.branch_id == branch_id,
    )

    result = db.execute(stmt)
    existing = result.scalars().first()


    if existing:
        return {
            "message": "Schedule already exists",
            "id": existing.id,
            "start_time": existing.start_time.strftime("%H:%M:%S"),
            "end_time": existing.end_time.strftime("%H:%M:%S"),
        }

    schedule = DoctorSchedule(
        doctor_id=doctor_id,
        schedule_date=date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj,
        slot_minutes=slot_minutes,
        max_patients=max_patients,
        hospital_id=hospital_id,
        branch_id=branch_id,
    )

    db.add(schedule)

    db.commit()
    db.refresh(schedule)

    return {
        "id": schedule.id,
        "doctor_id": schedule.doctor_id,
        "schedule_date": str(schedule.schedule_date),
        "start_time": schedule.start_time.strftime("%H:%M:%S"),
        "end_time": schedule.end_time.strftime("%H:%M:%S"),
        "slot_minutes": schedule.slot_minutes,
        "max_patients": schedule.max_patients,
        "hospital_id": schedule.hospital_id,
        "branch_id": schedule.branch_id,
    }

@router.post(
    "/availability/upload",
    response_model=list[AvailabilitySlotOut],
    dependencies=[Depends(require_roles("receptionist","front_office","admin","superadmin","doctor"))]
)
def upload_availability(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db)
):
    service = AppointmentService(db, tenant)

    # read excel
    df = pd.read_excel(file.file)

    results = []

    for _, row in df.iterrows():
        doctor_id = int(row["doctor_id"])
        for_date = pd.to_datetime(row["for_date"]).date()

        data = service.availability(doctor_id, for_date)
        results.extend(data)

    return results



@router.get(
    "",
    response_model=AppointmentListOut,
    dependencies=[Depends(require_roles(
        "receptionist",
        "front_office",
        "admin",
        "superadmin",
        "doctor",
        "branch_admin",
        "nurse"
    ))]
)
def list_appts(
    doctor_id: int | None = None,
    patient_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 20

    items, total = AppointmentService(db, tenant).list_appointments(
        doctor_id=doctor_id,
        patient_id=patient_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }



@router.get("/{appt_id}", response_model=AppointmentDetailOut,
            dependencies=[Depends(require_roles("receptionist","front_office","admin","superadmin","doctor","branch_admin","nurse"))])
def get_appt(appt_id: int,
             tenant: Tenant = Depends(get_tenant),
             db: Session = Depends(get_db)):
    return AppointmentService(db, tenant).get_by_id(appt_id)


@router.post("/{appt_id}/cancel", response_model=AppointmentCancelIn,
             dependencies=[Depends(require_roles("receptionist","front_office","admin","superadmin","accountant","branch_admin"))])
def cancel_appt(appt_id: int, payload: AppointmentCancelIn,
                tenant: Tenant = Depends(get_tenant), db: Session = Depends(get_db)):
    return AppointmentService(db, tenant).cancel(
        appt_id=appt_id,
        reason=payload.reason,
        do_refund=payload.refund,
        refund_amount=payload.refund_amount,
        refund_mode=payload.refund_mode,
        refund_cash_500=payload.refund_cash_500,
        refund_cash_200=payload.refund_cash_200,
        refund_cash_100=payload.refund_cash_100,
        refund_cash_50=payload.refund_cash_50,
        refund_cash_20=payload.refund_cash_20,
        refund_cash_10=payload.refund_cash_10,
        refund_cash_5=payload.refund_cash_5,
        refund_cash_2=payload.refund_cash_2,
        refund_cash_1=payload.refund_cash_1,
        refund_utr_no=payload.refund_utr_no,
    )



@router.post(
    "",
    response_model=AppointmentOutIDs,
    dependencies=[Depends(require_roles(
        "receptionist", "front_office", "branch_admin", "admin", "superadmin"
    ))]
)
def create_appt(
    patient_id: int = Form(...),
    doctor_id: int = Form(...),
    schedule_date: datetime = Form(...),

    visit_type: str = Form(...),
    shift: str = Form(...),
    slot_label: str = Form(...),
    priority: PriorityEnum = Form(...),

    # changed default
    payment_mode: str | None = Form("pay_at_hospital"),
    payment_status: str | None = Form("pending"),

    phone_number: int = Form(...),
    doctor_fee: int | None = Form(None),
    discount_pct: int | None = Form(0),
    is_video: bool | None = Form(False),
    status: str | None = Form("booked"),
    notes: str | None = Form(None),
    coins: str | None = Form(None),

    gender: str = Form(...),
    blood_group: str = Form(...),
    ward_name: str | None = Form(None),

    cash_500: int | None = Form(0),
    cash_200: int | None = Form(0),
    cash_100: int | None = Form(0),
    cash_50: int | None = Form(0),
    cash_20: int | None = Form(0),
    cash_10: int | None = Form(0),
    cash_5: int | None = Form(0),
    cash_2: int | None = Form(0),
    cash_1: int | None = Form(0),
    utr_no: str | None = Form(None),

    patient_name: str | None = Form(None),
    doctor_name: str | None = Form(None),
    department: str | None = Form(None),
    discount_reason: str | None = Form(None),
    referral_name: str | None = Form(None),
    referral_amount: int | None = Form(0),
    prev_med_history: Optional[Union[UploadFile, str]] = File(None),

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    med_path = ""

    if prev_med_history:
        med_path = upload_to_s3(
            upload=prev_med_history,
            folder="medical_history"
        )

    payload = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        schedule_date=schedule_date,

        visit_type=visit_type,
        shift=shift,
        slot_label=slot_label,
        priority=priority,

        payment_mode=payment_mode.strip(),
        payment_status=payment_status,

        phone_number=phone_number,
        doctor_fee=doctor_fee,
        discount_pct=discount_pct,
        is_video=is_video,
        status=status,
        notes=notes,
        coins=coins,

        gender=gender,
        blood_group=blood_group,
        ward_name=ward_name,

        cash_500=cash_500,
        cash_200=cash_200,
        cash_100=cash_100,
        cash_50=cash_50,
        cash_20=cash_20,
        cash_10=cash_10,
        cash_5=cash_5,
        cash_2=cash_2,
        cash_1=cash_1,
        utr_no=utr_no,

        patient_name=patient_name,
        doctor_name=doctor_name,
        department=department,
        discount_reason=discount_reason,
        referral_name=referral_name,
        referral_amount=referral_amount,

    )

    return AppointmentService(db, tenant).book(
        payload,
        med_history_file_path=med_path
    )




@router.put(
    "/{appointment_id}",
    response_model=AppointmentOutIDs,
    dependencies=[Depends(require_roles(
        "receptionist", "front_office", "branch_admin", "admin", "superadmin"
    ))]
)
def update_appt(
    appointment_id: int,

    patient_id: int | None = Form(None),
    doctor_id: int | None = Form(None),
    schedule_date: datetime | None = Form(None),

    visit_type: str | None = Form(None),
    shift: str | None = Form(None),
    slot_label: str | None = Form(None),
    priority: PriorityEnum | None = Form(None),

    payment_mode: str | None = Form(None),
    payment_status: str | None = Form(None),

    phone_number: int | None = Form(None),
    doctor_fee: int | None = Form(None),
    discount_pct: int | None = Form(None),
    is_video: bool | None = Form(None),
    status: str | None = Form(None),
    notes: str | None = Form(None),
    coins: str | None = Form(None),

    gender: str | None = Form(None),
    blood_group: str | None = Form(None),
    ward_name: str | None = Form(None),

    cash_500: int | None = Form(None),
    cash_200: int | None = Form(None),
    cash_100: int | None = Form(None),
    cash_50: int | None = Form(None),
    cash_20: int | None = Form(None),
    cash_10: int | None = Form(None),
    cash_5: int | None = Form(None),
    cash_2: int | None = Form(None),
    cash_1: int | None = Form(None),
    utr_no: str | None = Form(None),

    patient_name: str | None = Form(None),
    doctor_name: str | None = Form(None),
    department: str | None = Form(None),
    discount_reason: str | None = Form(None),
    referral_name: str | None = Form(None),
    referral_amount: int | None = Form(None),

    prev_med_history: UploadFile | None = File(None),

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db, tenant)

    appointment = service.get_by_id(appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )


    payload = AppointmentCreate(
        patient_id=patient_id,
        doctor_id=doctor_id,
        schedule_date=schedule_date,

        visit_type=visit_type,
        shift=shift,
        slot_label=slot_label,
        priority=priority,

        payment_mode=payment_mode,
        payment_status=payment_status,

        phone_number=phone_number,
        doctor_fee=doctor_fee,
        discount_pct=discount_pct,
        is_video=is_video,
        status=status,
        notes=notes,
        coins=coins,

        gender=gender,
        blood_group=blood_group,
        ward_name=ward_name,

        cash_500=cash_500,
        cash_200=cash_200,
        cash_100=cash_100,
        cash_50=cash_50,
        cash_20=cash_20,
        cash_10=cash_10,
        cash_5=cash_5,
        cash_2=cash_2,
        cash_1=cash_1,
        utr_no=utr_no,

        patient_name=patient_name,
        doctor_name=doctor_name,
        department=department,
        discount_reason=discount_reason,
        referral_name=referral_name,
        referral_amount=referral_amount,
    )

    med_path = None

    if prev_med_history:
        med_path = upload_to_s3(
            upload=prev_med_history,
            folder="medical_history"
        )

    payload_dict = payload.model_dump(exclude_none=True)

    if med_path:
        payload_dict["med_history_file_path"] = med_path

    return service.update(
        appt_id=appointment_id,
        payload=payload_dict
    )

@router.delete(
    "/{appointment_id}",
    status_code=200,
    dependencies=[Depends(require_roles(
        "branch_admin",
        "admin",
        "superadmin"
    ))]
)
def delete_appt(
        appointment_id: int,
        tenant: Tenant = Depends(get_tenant),
        db: Session = Depends(get_db),
):
    service = AppointmentService(db, tenant)

    appointment = service.get_by_id(appointment_id)

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    service.delete(appointment_id)

    return {
        "success": True,
        "message": "Appointment deleted successfully"
    }


@router.get(
    "/doctors/{doctor_id}/patients",
    dependencies=[Depends(require_roles(
        "receptionist",
        "doctor",
        "nurse",
        "accountant",
        "admin",
        "superadmin"
    ))]
)
def get_doctor_patients(
    doctor_id: int,
    from_date: date,
    to_date: date,

    tenant: Tenant = Depends(get_tenant),
    db: Session = Depends(get_db),
):
    stmt = (
        select(
            Patient.id.label("patient_id"),

            Patient.first_name,
            Patient.last_name,

            Patient.age,
            Patient.gender,

            Patient.phone_number,
            Patient.email,

            Patient.location,
            Patient.blood_group,

            Appointment.id.label("appointment_id"),
            Appointment.schedule_date,
            Appointment.status,
        )
        .join(
            Appointment,
            Appointment.patient_id == Patient.id
        )
        .where(
            Appointment.doctor_id == doctor_id,

            func.date(Appointment.schedule_date) >= from_date,
            func.date(Appointment.schedule_date) <= to_date,

            Patient.hospital_id == tenant.hospital_id,
            Appointment.branch_id == tenant.branch_id,
        )
        .order_by(
            Appointment.schedule_date.asc(),
        )
    )

    rows = db.execute(stmt).all()

    return {
        "doctor_id": doctor_id,
        "from_date": from_date,
        "to_date": to_date,

        "total_patients": len(rows),

        "patient_list": [
            {
                "patient_id": row.patient_id,

                "name": f"{row.first_name} {row.last_name or ''}".strip(),

                "age": row.age,
                "gender": row.gender,

                "mobile_number": row.phone_number,
                "email": row.email,

                "address": row.location,
                "blood_group": row.blood_group,

                "appointment_id": row.appointment_id,
                "schedule_date": row.schedule_date,

                "status": row.status,
            }
            for row in rows
        ]
    }