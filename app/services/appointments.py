from datetime import datetime, date, timedelta
from fastapi import HTTPException
from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session
from app.core.settings import settings
from app.models.appointments import Appointment
from app.models.schedule import DoctorSchedule
from app.models.people import Doctor, Patient, Staff
from app.services.admin_people import _bad
from app.utils.tenant import Tenant


# from app.models.opd import OPDVisits

def _ensure_non_negative(*values: int) -> None:
    for v in values:
        if v is not None and v < 0:
            raise HTTPException(status_code=400, detail="Denomination counts cannot be negative")


def _sum_cash(c500=0, c200=0, c100=0, c50=0, c20=0, c10=0, c5=0, c2=0, c1=0) -> int:
    return int(c500 or 0) * 500 + int(c200 or 0) * 200 + int(c100 or 0) * 100 + int(c50 or 0) * 50 + int(
        c20 or 0) * 20 + int(c10 or 0) * 10 + int(c5 or 0) * 5 + int(c2 or 0) * 2 + int(c1 or 0) * 1


class AppointmentService:
    def __init__(self, db: Session, tenant: Tenant) -> None:
        self.db = db
        self.tenant = tenant

    # ---------- availability / conflict checks ----------
    def _doctor_available(self, doctor_id: int, when: datetime) -> bool:
        dow = when.weekday()  # 0=Mon
        print("@@@@@@@@@@", when)
        q = select(DoctorSchedule).where(
            and_(
                DoctorSchedule.hospital_id == self.tenant.hospital_id,
                DoctorSchedule.branch_id == self.tenant.branch_id,
                DoctorSchedule.doctor_id == doctor_id,
                DoctorSchedule.schedule_date == when.date(),
                DoctorSchedule.start_time <= when.time(),
                DoctorSchedule.end_time > when.time(),
            )
        )
        # print("@@@@@@@@@@@@@@@",self.db.execute(q).scalar_one_or_none())
        row = self.db.execute(q).scalar_one_or_none()
        print("data of the 22222222222", row)

        print("doctor:", doctor_id)
        print("dow:", dow)
        print("time:", when.time())
        print("result:", row)

        return row is not None
        # return self.db.execute(q).scalar_one_or_none() is not None

    def _not_double_booked(self, doctor_id: int, when: datetime) -> bool:
        q = select(Appointment).where(
            and_(
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
                Appointment.doctor_id == doctor_id,
                Appointment.schedule_date == when,
                Appointment.status.in_(["booked", "confirmed", "arrived"]),
            )
        )
        return self.db.execute(q).scalar_one_or_none() is None

    #
    # avalablity for all doctors
    from datetime import datetime, time, timedelta
    from sqlalchemy import select

    def availability_all_doctors(self, date):

        doctors_result = self.db.execute(
            select(Doctor).where(
                Doctor.hospital_id == self.tenant.hospital_id
            )
        )

        doctors = doctors_result.scalars().all()

        result = []

        for doctor in doctors:

            schedule_result = self.db.execute(
                select(DoctorSchedule).where(
                    DoctorSchedule.hospital_id == self.tenant.hospital_id,
                    DoctorSchedule.branch_id == self.tenant.branch_id,
                    DoctorSchedule.doctor_id == doctor.id,
                    DoctorSchedule.schedule_date == date,
                )
            )

            schedule = schedule_result.scalar_one_or_none()

            if not schedule:
                result.append({
                    "doctor_id": doctor.id,
                    "doctor_code": doctor.doctor_code,
                    "slots": []
                })
                continue

            start = datetime.combine(date, schedule.start_time)
            end = datetime.combine(date, schedule.end_time)

            slots = []
            current = start

            while current < end:
                slots.append({
                    "start": current.isoformat(),
                    "end": (current + timedelta(minutes=15)).isoformat(),
                    "available": self._not_double_booked(
                        doctor.id,
                        current
                    )
                })

                current += timedelta(minutes=15)

            result.append({
                "doctor_id": doctor.id,
                "doctor_code": doctor.doctor_code,
                "slots": slots
            })

        return result


    def book(self, payload, med_history_file_path: str = "") -> Appointment:
        doc_id = int(payload.doctor_id)
        pat_id = int(payload.patient_id)

        # Phone validation
        if payload.phone_number:
            phone = str(payload.phone_number).strip()

            if not (phone.isdigit() and len(phone) == 10):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number must contain exactly 10 digits"
                )

        # Prevent booking past date/time
        current_time = datetime.now()

        if payload.schedule_date < current_time:
            raise HTTPException(
                status_code=400,
                detail="Cannot book an appointment for a past date/time."
            )

        # Doctor availability
        if not self._doctor_available(doc_id, payload.schedule_date):
            raise HTTPException(
                status_code=400,
                detail="Doctor not available at this time"
            )

        # Doctor fee validation
        if payload.doctor_fee is not None and payload.doctor_fee < 0:
            raise HTTPException(
                status_code=400,
                detail="Doctor fee cannot be negative"
            )

        # Discount validation
        if payload.discount_pct is not None:
            if payload.discount_pct < 0 or payload.discount_pct > 100:
                raise HTTPException(
                    status_code=400,
                    detail="Discount percentage must be between 0 and 100"
                )

        # Referral amount validation
        if payload.referral_amount is not None and payload.referral_amount < 0:
            raise HTTPException(
                status_code=400,
                detail="Referral amount cannot be negative"
            )

        # UTR validation
        if payload.utr_no and len(payload.utr_no.strip()) > 50:
            raise HTTPException(
                status_code=400,
                detail="UTR number cannot exceed 50 characters"
            )

        if not  self._doctor_available(doc_id, payload.schedule_date):
            raise HTTPException(status_code=400, detail="Doctor not available at this time")

        if not self._not_double_booked(doc_id, payload.schedule_date):
            raise HTTPException(status_code=400, detail="Slot already booked")

        fee = payload.doctor_fee
        if fee is None:
            d =  self.db.get(Doctor, doc_id)
            fee = d.consultation_fee if d else 0

        priority = (payload.priority or "Normal").capitalize()
        if fee is not None and priority == "Emergency":
            fee = int(round(fee * (1 + settings.APPT_EMERGENCY_SURCHARGE_PERCENT / 100)))

        discount_pct = payload.discount_pct or 0
        discount_amt = int(round((discount_pct / 100) * fee)) if fee else 0
        amount_payable = max(0, int(fee) - discount_amt)

        payment_mode = (payload.payment_mode or "pay_at_hospital")

        cash_total = 0
        change_amount = 0
        utr_no = None
        payment_status = "pending"

        if payment_mode in ["pay_at_hospital", "pending", "later"]:
            payment_mode = "pay_at_hospital"
            payment_status = "pending"

        elif payment_mode == "Cash":
            _ensure_non_negative(
                payload.cash_500,
                payload.cash_200,
                payload.cash_100,
                payload.cash_50,
                payload.cash_20,
                payload.cash_10,
                payload.cash_5,
                payload.cash_2,
                payload.cash_1,
            )

            cash_total = _sum_cash(
                payload.cash_500,
                payload.cash_200,
                payload.cash_100,
                payload.cash_50,
                payload.cash_20,
                payload.cash_10,
                payload.cash_5,
                payload.cash_2,
                payload.cash_1,
            )

            if cash_total <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Provide cash denominations for Cash payment"
                )

            if cash_total < amount_payable:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cash total ({cash_total}) is less than payable amount ({amount_payable})"
                )

            change_amount = cash_total - amount_payable
            payment_status = "paid"

        else:
            utr_no = (payload.utr_no or "").strip()
            if not utr_no:
                raise HTTPException(
                    status_code=400,
                    detail="UTR/reference number is required for non-cash payments"
                )

            payment_status = "paid"

        p =  self.db.get(Patient, pat_id)
        d =  self.db.get(Doctor, doc_id)
        d_staff = self.db.get(Staff, d.staff_id) if d and d.staff_id else None

        patient_name_snapshot = payload.patient_name or (
            f"{p.first_name} {p.last_name or ''}".strip() if p else None
        )

        doctor_name_snapshot = payload.doctor_name or (
            f"{(d_staff.first_name if d_staff else '')} {(d_staff.last_name if d_staff else '')}".strip()
            if d else None
        )

        existing_appt = self.db.execute(
            select(Appointment).where(
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
                Appointment.patient_id == pat_id,
                Appointment.doctor_id == doc_id,
                Appointment.schedule_date == payload.schedule_date
            )
        ).scalars().first()

        if existing_appt:
            raise HTTPException(
                status_code=400,
                detail="Appointment already exists for this patient, doctor and slot"
            )

        appt = Appointment(
            hospital_id=self.tenant.hospital_id,
            branch_id=self.tenant.branch_id,

            appointment_no="TEMP",
            patient_id=pat_id,
            doctor_id=doc_id,

            phone_number=payload.phone_number,
            schedule_date=payload.schedule_date,

            status=payload.status or "booked",
            payment_status=payment_status,

            notes=payload.notes,
            shift=payload.shift,
            slot_label=payload.slot_label,
            priority=priority,

            payment_mode=payment_mode,
            doctor_fee=int(fee or 0),
            discount_pct=int(discount_pct),
            is_video=bool(payload.is_video),
            amount_payable=amount_payable,

            cash_500=int(payload.cash_500 or 0),
            cash_200=int(payload.cash_200 or 0),
            cash_100=int(payload.cash_100 or 0),
            cash_50=int(payload.cash_50 or 0),
            cash_20=int(payload.cash_20 or 0),
            cash_10=int(payload.cash_10 or 0),
            cash_5=int(payload.cash_5 or 0),
            cash_2=int(payload.cash_2 or 0),
            cash_1=int(payload.cash_1 or 0),

            cash_total=cash_total,
            change_amount=change_amount,
            utr_no=utr_no or None,

            gender=payload.gender,
            ward_name=payload.ward_name,
            blood_group=payload.blood_group,

            patient_name_snapshot=patient_name_snapshot,
            doctor_name_snapshot=doctor_name_snapshot,

            department=payload.department,
            discount_reason=payload.discount_reason,
            referral_name=payload.referral_name,
            referral_amount=int(payload.referral_amount or 0),
            med_history_file_path=med_history_file_path or None,
        )

        try:
            self.db.add(appt)
            self.db.flush()

            appt.appointment_no = f"APT{payload.schedule_date:%y%m}{appt.id:05d}"

            self.db.commit()

        except Exception as e:
            print("error occurred while booking appointment:", e)
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Slot just got booked by someone else"
            )

        self.db.refresh(appt)
        return appt

    def list_appointments(
            self,
            doctor_id,
            patient_id,
            date_from,
            date_to,
            page,
            page_size
    ) -> tuple[list[dict], int]:

        base = (
            select(
                Appointment,
                Patient.first_name.label("p_fn"),
                Patient.last_name.label("p_ln"),
                Patient.patient_code.label("patient_code"),
                Patient.age.label("patient_age"),
                Patient.phone_number.label("patient_phone"),
                Patient.email.label("patient_email"),
                Patient.location.label("patient_location"),
                Patient.blood_group.label("patient_blood_group"),

                Doctor.doctor_code.label("doctor_code"),
                Staff.first_name.label("d_fn"),
                Staff.last_name.label("d_ln"),
            )
            .join(Patient, Patient.id == Appointment.patient_id)
            .join(Doctor, Doctor.id == Appointment.doctor_id)
            .join(Staff, Staff.id == Doctor.staff_id)
            .where(
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
            )
        )

        if doctor_id is not None:
            base = base.where(Appointment.doctor_id == doctor_id)

        if patient_id is not None:
            base = base.where(Appointment.patient_id == patient_id)

        if date_from is not None:
            base = base.where(func.date(Appointment.schedule_date) >= date_from)

        if date_to is not None:
            base = base.where(func.date(Appointment.schedule_date) <= date_to)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int(self.db.execute(count_stmt).scalar() or 0)

        stmt = (
            base
            .order_by(Appointment.schedule_date.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = self.db.execute(stmt).all()

        items: list[dict] = []

        for row in result:
            appt: Appointment = row[0]

            p_name = appt.patient_name_snapshot or f"{row.p_fn} {row.p_ln or ''}".strip()
            d_name = appt.doctor_name_snapshot or f"{row.d_fn} {row.d_ln or ''}".strip()

            items.append(
                {
                    "id": appt.id,
                    "appointment_no": appt.appointment_no,

                    "patient_name": p_name,
                    "doctor_name": d_name,

                    "doctor_id": appt.doctor_id,
                    "patient_id": appt.patient_id,

                    "patient_code": row.patient_code,
                    "patient_age": row.patient_age,
                    "patient_email": row.patient_email,
                    "patient_address": row.patient_location,

                    "schedule_date": appt.schedule_date,
                    "status": appt.status,

                    "phone_number": appt.phone_number or row.patient_phone,

                    "shift": appt.shift,
                    "slot_label": appt.slot_label,
                    "priority": appt.priority,

                    "payment_mode": appt.payment_mode,
                    "doctor_fee": appt.doctor_fee,
                    "discount_pct": appt.discount_pct,
                    "is_video": appt.is_video,
                    "amount_payable": appt.amount_payable,
                    "utr_no": appt.utr_no,
                    "cash_total": appt.cash_total,

                    "blood_group": appt.blood_group or row.patient_blood_group,
                    "ward_name": appt.ward_name,
                    "gender": appt.gender,

                    "department": appt.department,
                    "discount_reason": appt.discount_reason,
                    "referral_name": appt.referral_name,
                    "referral_amount": appt.referral_amount,
                    "med_history_file_path": appt.med_history_file_path,
                }
            )

        return items, total

    def get_by_id(self, appt_id: int) -> dict:
        stmt = (
            select(
                Appointment,

                # Patient fields
                Patient.first_name.label("p_fn"),
                Patient.last_name.label("p_ln"),
                Patient.age.label("p_age"),

                # Doctor fields
                Staff.first_name.label("d_fn"),
                Staff.last_name.label("d_ln"),
            )

            # OUTER JOIN patient
            .outerjoin(Patient, Patient.id == Appointment.patient_id)

            .join(Doctor, Doctor.id == Appointment.doctor_id)
            .join(Staff, Staff.id == Doctor.staff_id)

            .where(
                Appointment.id == appt_id,
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
            )
        )

        row = self.db.execute(stmt).first()

        if not row:
            raise HTTPException(status_code=404, detail="Appointment not found")

        appt: Appointment = row[0]

        p_name = appt.patient_name_snapshot or f"{row.p_fn} {row.p_ln}".strip()
        d_name = appt.doctor_name_snapshot or f"{row.d_fn} {row.d_ln}".strip()

        return {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "appointment_no": appt.appointment_no,
            "patient_name": p_name,

            # age from Patient table
            "age": row.p_age,

            "gender": getattr(appt, "gender", None),
            "blood_group": getattr(appt, "blood_group", None),
            "ward_name": getattr(appt, "ward_name", None),
            "doctor_name": d_name,

            "schedule_date": appt.schedule_date,

            "status": appt.status,
            "shift": appt.shift,
            "slot_label": appt.slot_label,
            "priority": appt.priority,
            "payment_mode": appt.payment_mode,
            "doctor_fee": appt.doctor_fee,
            "discount_pct": appt.discount_pct,
            "is_video": appt.is_video,
            "amount_payable": appt.amount_payable,
            "utr_no": appt.utr_no,
            "cash_total": appt.cash_total,
            "doctor_id": appt.doctor_id,

            "cash_denomination": {
                "500": appt.cash_500,
                "200": appt.cash_200,
                "100": appt.cash_100,
                "50": appt.cash_50,
                "20": appt.cash_20,
                "10": appt.cash_10,
                "5": appt.cash_5,
                "2": appt.cash_2,
                "1": appt.cash_1,
            },

            "cancelled_at": appt.cancelled_at,
            "cancel_reason": appt.cancel_reason,
            "refund_amount": appt.refund_amount,
            "refund_mode": appt.refund_mode,

            "department": appt.department,
            "discount_reason": appt.discount_reason,
            "referral_name": appt.referral_name,
            "referral_amount": appt.referral_amount,
            "med_history_file_path": appt.med_history_file_path,
        }

    def get_appointment_model(self, appointment_id: int):
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
            )
            .first()
        )

    # def update(self, appt_id: int, payload: dict):
    #     appt = self.db.get(Appointment, appt_id)
    #
    #     if not appt:
    #         raise HTTPException(status_code=404, detail="Appointment not found")
    #
    #     # fields that should never be overwritten
    #     protected_fields = {"id", "appointment_no", "branch_id", "doctor_id"}
    #
    #     for key, value in payload.items():
    #         if key in protected_fields:
    #             continue
    #
    #         if value is not None and hasattr(appt, key):
    #             setattr(appt, key, value)
    #
    #     self.db.commit()
    #     self.db.refresh(appt)
    #     return appt

    def update(self, appt_id: int, payload: dict):
        appt = self.db.get(Appointment, appt_id)

        if not appt:
            raise HTTPException(
                status_code=404,
                detail="Appointment not found"
            )

        # Phone validation
        if payload.get("phone_number"):
            phone = str(payload["phone_number"]).strip()

            if not (phone.isdigit() and len(phone) == 10):
                raise HTTPException(
                    status_code=400,
                    detail="Phone number must contain exactly 10 digits"
                )

        # Doctor fee validation
        if payload.get("doctor_fee") is not None:
            if payload["doctor_fee"] < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Doctor fee cannot be negative"
                )

        # Discount validation
        if payload.get("discount_pct") is not None:
            if payload["discount_pct"] < 0 or payload["discount_pct"] > 100:
                raise HTTPException(
                    status_code=400,
                    detail="Discount percentage must be between 0 and 100"
                )

        # Referral amount validation
        if payload.get("referral_amount") is not None:
            if payload["referral_amount"] < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Referral amount cannot be negative"
                )

        # UTR validation
        if payload.get("utr_no"):
            utr_no = str(payload["utr_no"]).strip()

            if len(utr_no) > 50:
                raise HTTPException(
                    status_code=400,
                    detail="UTR number cannot exceed 50 characters"
                )

        # Cash denomination validation
        cash_fields = [
            "cash_500", "cash_200", "cash_100",
            "cash_50", "cash_20", "cash_10",
            "cash_5", "cash_2", "cash_1"
        ]

        for field in cash_fields:
            value = payload.get(field)

            if value is not None and value < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} cannot be negative"
                )

        protected_fields = {"id", "appointment_no", "branch_id", "doctor_id"}

        # Duplicate appointment validation
        patient_id = payload.get("patient_id", appt.patient_id)

        if patient_id is None:
            raise HTTPException(
                status_code=400,
                detail="Patient ID cannot be null"
            )

        schedule_date = payload.get("schedule_date", appt.schedule_date)

        duplicate = self.db.execute(
            select(Appointment).where(
                Appointment.id != appt_id,
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
                Appointment.doctor_id == appt.doctor_id,
                Appointment.patient_id == patient_id,
                Appointment.schedule_date == schedule_date
            )
        ).scalars().first()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Appointment already exists for this patient, doctor and slot"
            )

        payment_mode = payload.get("payment_mode")

        if payment_mode:
            payment_mode_lower = payment_mode.lower()
            amount_payable = appt.amount_payable or 0

            if payment_mode_lower == "cash":
                cash_total = _sum_cash(
                    payload.get("cash_500") or 0,
                    payload.get("cash_200") or 0,
                    payload.get("cash_100") or 0,
                    payload.get("cash_50") or 0,
                    payload.get("cash_20") or 0,
                    payload.get("cash_10") or 0,
                    payload.get("cash_5") or 0,
                    payload.get("cash_2") or 0,
                    payload.get("cash_1") or 0,
                )

                if cash_total < amount_payable:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Cash total ({cash_total}) is less than payable amount ({amount_payable})"
                    )

                payload["cash_total"] = cash_total
                payload["change_amount"] = cash_total - amount_payable
                payload["payment_status"] = "paid"
                payload["payment_mode"] = "Cash"

            elif payment_mode_lower == "upi":
                utr_no = (payload.get("utr_no") or "").strip()
                if not utr_no:
                    raise HTTPException(
                        status_code=400,
                        detail="UTR/reference number is required"
                    )

                payload["payment_status"] = "paid"
                payload["payment_mode"] = "UPI"
                payload["utr_no"] = utr_no

            elif payment_mode_lower == "card":
                payload["payment_status"] = "paid"
                payload["payment_mode"] = "Card"

            elif payment_mode_lower == "online":
                utr_no = (payload.get("utr_no") or "").strip()
                if not utr_no:
                    raise HTTPException(
                        status_code=400,
                        detail="UTR/reference number is required"
                    )

                payload["payment_status"] = "paid"
                payload["payment_mode"] = "Online"
                payload["utr_no"] = utr_no

            elif payment_mode_lower in ["pay_at_hospital", "pending", "later"]:
                payload["payment_status"] = "pending"
                payload["payment_mode"] = "pay_at_hospital"

        for key, value in payload.items():
            if key in protected_fields:
                continue

            if value is not None and hasattr(appt, key):
                setattr(appt, key, value)

        self.db.commit()
        self.db.refresh(appt)
        return appt

        # ---------------- DELETE ----------------

    def delete(self, appt_id: int):
        appt = self.db.get(Appointment, appt_id)
        try:
            if not appt:
                raise HTTPException(status_code=404, detail="Appointment not found")

            self.db.delete(appt)
            self.db.commit()

            return {"message": "Appointment deleted successfully"}
        except:
            raise HTTPException(status_code=409,
                                detail="Appointment could not be deleted! already this appointment patient visited to doctor")
    #
    # from datetime import datetime, timedelta, date
    # from sqlalchemy import select, and_

    def availability(self, doctor_id: int, for_date: date) -> list[dict]:
        result = self.db.execute(
            select(DoctorSchedule).where(
                and_(
                    DoctorSchedule.hospital_id == self.tenant.hospital_id,
                    DoctorSchedule.branch_id == self.tenant.branch_id,
                    DoctorSchedule.doctor_id == doctor_id,
                    DoctorSchedule.schedule_date == for_date,
                )
            )
        )

        scheds = result.scalars().all()

        if not scheds:
            return []

        start_dt = datetime.combine(for_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)

        booked_result = self.db.execute(
            select(Appointment.schedule_date).where(
                and_(
                    Appointment.hospital_id == self.tenant.hospital_id,
                    Appointment.branch_id == self.tenant.branch_id,
                    Appointment.doctor_id == doctor_id,
                    Appointment.schedule_date >= start_dt,
                    Appointment.schedule_date < end_dt,
                    Appointment.status.in_(["booked", "confirmed", "arrived"]),
                )
            )
        )

        booked = {row[0] for row in booked_result.all()}

        slots = []

        for s in scheds:
            cur = datetime.combine(for_date, s.start_time)
            end = datetime.combine(for_date, s.end_time)
            step = timedelta(minutes=int(s.slot_minutes or 15))

            while cur < end:
                nxt = cur + step

                slots.append(
                    {
                        "start": cur.isoformat(),
                        "end": nxt.isoformat(),
                        "label": f"{cur:%H:%M}-{nxt:%H:%M}",
                        "available": cur not in booked,
                    }
                )

                cur = nxt

        return slots

    def create_availability(self, doctor_id, for_date, start_time, end_time, slot_minutes: int = 20,
                            max_patients: int = 10
                            ):

        # calculate day_of_week
        # day_of_week = for_date.weekday()

        # check doctor exists
        doctor = self.db.get(Doctor, doctor_id)
        if not doctor:
            raise _bad("Doctor not found", 404)

        duplicate = self.db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.schedule_date == for_date,
            DoctorSchedule.start_time == start_time,
            DoctorSchedule.end_time == end_time,
            DoctorSchedule.hospital_id == self.tenant.hospital_id,
            DoctorSchedule.branch_id == self.tenant.branch_id,
        ).first()

        if duplicate:
            raise HTTPException(
                status_code=400,
                detail="Availability already exists for this doctor and time slot"
            )

        #  prevent overlapping slots
        existing = self.db.query(DoctorSchedule).filter(
            DoctorSchedule.doctor_id == doctor_id,
            # DoctorSchedule.day_of_week == day_of_week,
            DoctorSchedule.schedule_date == for_date,
            DoctorSchedule.hospital_id == self.tenant.hospital_id,
            DoctorSchedule.branch_id == self.tenant.branch_id,
            # DoctorSchedule.slot_minutes == self.slot_minutes,
            DoctorSchedule.max_patients == max_patients,
            DoctorSchedule.start_time < end_time,
            DoctorSchedule.end_time > start_time
        ).first()

        if existing:
            raise _bad("Time slot overlaps with existing availability")

        #  create slot
        slot = DoctorSchedule(
            doctor_id=doctor_id,
            # day_of_week=day_of_week,
            schedule_date=for_date,
            for_date=for_date,
            start_time=start_time,
            slot_minutes=20,
            # slot_minutes=slot_minutes,
            end_time=end_time,
            max_patients=max_patients,
            hospital_id=self.tenant.hospital_id,
            branch_id=self.tenant.branch_id
        )
        self._apply_tenant(slot)
        self.db.add(slot)
        self.db.commit()
        self.db.refresh(slot)

        return {
            "id": slot.id,
            "doctor_id": doctor_id,
            "for_date": for_date,
            "start_time": start_time,
            "schedule_date": for_date,
            "end_time": end_time,
            "hospital_id": self.tenant.hospital_id,
            "branch_id": self.tenant.branch_id,
            "slot_minutes": slot_minutes,
            "max_patients": max_patients,
        }

    def cancel(
            self,
            appt_id: int,
            reason: str,
            do_refund: bool,
            refund_amount: int | None,
            refund_mode: str | None,
            refund_cash_500: int | None = 0,
            refund_cash_200: int | None = 0,
            refund_cash_100: int | None = 0,
            refund_cash_50: int | None = 0,
            refund_cash_20: int | None = 0,
            refund_cash_10: int | None = 0,
            refund_cash_5: int | None = 0,
            refund_cash_2: int | None = 0,
            refund_cash_1: int | None = 0,
            refund_utr_no: str | None = None,
    ) -> dict:
        appt = self.db.execute(
            select(Appointment).where(
                Appointment.id == appt_id,
                Appointment.hospital_id == self.tenant.hospital_id,
                Appointment.branch_id == self.tenant.branch_id,
            )
        ).scalar_one_or_none()
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if appt.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Completed appointment cannot be cancelled"
            )

        if appt.status == "cancelled":
            return {
                "id": appt.id,
                "status": appt.status,
                "reason": reason,
                "cancelled_at": appt.cancelled_at,
                "refund_amount": appt.refund_amount,
                "refund_mode": appt.refund_mode,
                "refund_cash_total": appt.refund_cash_total,
                "refund_utr_no": appt.refund_utr_no,
            }

        appt.status = "cancelled"
        appt.cancel_reason = reason
        appt.cancelled_at = datetime.utcnow()

        if do_refund:
            effective_amount = refund_amount if refund_amount is not None else appt.amount_payable
            if effective_amount > (appt.amount_payable or 0):
                raise HTTPException(
                    status_code=400,
                    detail="Refund amount cannot exceed paid amount"
                )
            if (refund_mode or appt.payment_mode or "Cash") == "Cash":
                _ensure_non_negative(refund_cash_500, refund_cash_200, refund_cash_100, refund_cash_50, refund_cash_20,
                                     refund_cash_10, refund_cash_5, refund_cash_2, refund_cash_1)
                refund_cash_total = _sum_cash(refund_cash_500, refund_cash_200, refund_cash_100, refund_cash_50,
                                              refund_cash_20, refund_cash_10, refund_cash_5, refund_cash_2,
                                              refund_cash_1)
                if refund_cash_total <= 0:
                    raise HTTPException(status_code=400, detail="Provide cash denominations for cash refund")
                if refund_amount is not None and refund_cash_total != refund_amount:
                    raise HTTPException(status_code=400,
                                        detail=f"Refund cash total ({refund_cash_total}) does not match refund_amount ({refund_amount})")
                appt.refund_mode = "Cash"
                appt.refund_amount = effective_amount if refund_amount is not None else refund_cash_total
                appt.refund_cash_500 = int(refund_cash_500 or 0)
                appt.refund_cash_200 = int(refund_cash_200 or 0)
                appt.refund_cash_100 = int(refund_cash_100 or 0)
                appt.refund_cash_50 = int(refund_cash_50 or 0)
                appt.refund_cash_20 = int(refund_cash_20 or 0)
                appt.refund_cash_10 = int(refund_cash_10 or 0)
                appt.refund_cash_5 = int(refund_cash_5 or 0)
                appt.refund_cash_2 = int(refund_cash_2 or 0)
                appt.refund_cash_1 = int(refund_cash_1 or 0)
                appt.refund_cash_total = refund_cash_total
                appt.refund_utr_no = None
            else:
                ru = (refund_utr_no or "").strip()
                if not ru:
                    raise HTTPException(status_code=400, detail="refund_utr_no is required for non-cash refund")
                appt.refund_mode = refund_mode
                appt.refund_amount = effective_amount
                appt.refund_cash_500 = appt.refund_cash_200 = appt.refund_cash_100 = 0
                appt.refund_cash_50 = appt.refund_cash_20 = appt.refund_cash_10 = 0
                appt.refund_cash_5 = appt.refund_cash_2 = appt.refund_cash_1 = 0
                appt.refund_cash_total = 0
                appt.refund_utr_no = ru
        else:
            appt.refund_amount = None
            appt.refund_mode = None
            appt.refund_cash_total = 0
            appt.refund_utr_no = None
            appt.refund_cash_500 = appt.refund_cash_200 = appt.refund_cash_100 = 0
            appt.refund_cash_50 = appt.refund_cash_20 = appt.refund_cash_10 = 0
            appt.refund_cash_5 = appt.refund_cash_2 = appt.refund_cash_1 = 0

        self.db.commit()
        self.db.refresh(appt)
        return {
            "id": appt.id,
            "status": appt.status,
            "reason": reason,
            "cancelled_at": appt.cancelled_at,
            "refund_amount": appt.refund_amount,
            "refund_mode": appt.refund_mode,
            "refund_cash_total": appt.refund_cash_total,
            "refund_utr_no": appt.refund_utr_no,
        }
