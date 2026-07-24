from app.models.ambulance_billing  import ResourceUsage, Billing, Insurance
from fastapi import HTTPException


# ================== RESOURCE ==================

def add_resource(db, data):
    resource = ResourceUsage(**data.dict())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def get_resource(db, request_id):
    resource = db.query(ResourceUsage).filter(
        ResourceUsage.request_id == request_id
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource

# ================== BILLING ==================

def create_billing(db, data):
    bill = Billing(**data.dict())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def get_billing(db, request_id):
    return db.query(Billing).filter(
        Billing.request_id == request_id
    ).first()


# ================== INSURANCE ==================

def create_insurance(db, data):
    insurance = Insurance(**data.dict())
    db.add(insurance)
    db.commit()
    db.refresh(insurance)
    return insurance


def get_insurance(db, billing_id):
    return db.query(Insurance).filter(
        Insurance.billing_id == billing_id
    ).first()