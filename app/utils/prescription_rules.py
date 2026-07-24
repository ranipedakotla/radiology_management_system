from datetime import date

MAX_PRESCRIPTION_DAYS = 7  # OPD

def is_prescription_valid(prescription_date: date) -> bool:
    return (date.today() - prescription_date).days <= MAX_PRESCRIPTION_DAYS


import enum
from fastapi import HTTPException

from app.models.pharmacy import MedicineCategory


def validate_restricted_medicine(medicine, prescription_id):
    if medicine.category != MedicineCategory.NORMAL and not prescription_id:
        raise HTTPException(
            status_code=400,
            detail="Prescription is mandatory for restricted medicines"
        )


def calculate_total_cash(denoms):
    return (
            denoms.note_2000 * 2000 +
            denoms.note_500 * 500 +
            denoms.note_200 * 200 +
            denoms.note_100 * 100 +
            denoms.note_50 * 50 +
            denoms.note_20 * 20 +
            denoms.note_10 * 10 +
            denoms.coins
    )
