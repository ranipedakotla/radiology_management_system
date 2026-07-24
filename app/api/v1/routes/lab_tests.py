from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_db
from app.models.lab_tests import LabTest

from app.schemas.lab_tests import (
    LabTestCreate,
    LabTestUpdate,
    LabTestResponse,
    LabTestAvailabilityResponse
)


router = APIRouter(
    prefix="/lab_tests",
    tags=["Lab_Tests"]
)


# =====================================================
# 1. CREATE LAB TEST
# =====================================================
@router.post(
    "/",
    response_model=LabTestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_lab_test(
    lab_test: LabTestCreate,
    db: Session = Depends(get_db)
):

    # Check duplicate Test Type + Test Sub Type
    existing_lab_test = db.query(LabTest).filter(
        LabTest.test_type == lab_test.test_type,
        LabTest.test_sub_type == lab_test.test_sub_type
    ).first()

    if existing_lab_test:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lab Test already exists."
        )

    new_lab_test = LabTest(
        test_type=lab_test.test_type,
        test_sub_type=lab_test.test_sub_type,
        cost=lab_test.cost,
        body_part=lab_test.body_part,
        precautions=lab_test.precautions,
        id_proof_required=lab_test.id_proof_required
    )

    db.add(new_lab_test)

    db.commit()

    db.refresh(new_lab_test)

    return new_lab_test


# =====================================================
# 2. GET ALL LAB TESTS
# =====================================================
@router.get(
    "/",
    response_model=list[LabTestResponse]
)
def get_all_lab_tests(
    db: Session = Depends(get_db)
):

    lab_tests = db.query(LabTest).all()

    return lab_tests


# =====================================================
# 3. TEST SEARCH
# =====================================================
@router.get(
    "/search",
    response_model=list[LabTestResponse]
)
def search_lab_tests(
    test_type: str | None = None,
    test_sub_type: str | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(LabTest)

    # Search by Test Type
    if test_type:

        query = query.filter(
            LabTest.test_type.ilike(
                f"%{test_type}%"
            )
        )

    # Search by Test Sub Type
    if test_sub_type:

        query = query.filter(
            LabTest.test_sub_type.ilike(
                f"%{test_sub_type}%"
            )
        )

    return query.all()


# =====================================================
# 4. GET AVAILABLE TESTS
# =====================================================
@router.get(
    "/available",
    response_model=list[LabTestResponse]
)
def get_available_lab_tests(
    db: Session = Depends(get_db)
):

    tests = (
        db.query(LabTest)
        .filter(
            LabTest.is_active.is_(True)
        )
        .all()
    )

    return tests


# =====================================================
# 5. CHECK TEST AVAILABILITY
# =====================================================
@router.get(
    "/{lab_test_id}/availability",
    response_model=LabTestAvailabilityResponse
)
def check_lab_test_availability(
    lab_test_id: int,
    db: Session = Depends(get_db)
):

    lab_test = (
        db.query(LabTest)
        .filter(
            LabTest.id == lab_test_id
        )
        .first()
    )

    if not lab_test:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab Test not found."
        )

    return {
        "id": lab_test.id,

        "test_type": lab_test.test_type,

        "test_sub_type": lab_test.test_sub_type,

        "is_available": lab_test.is_active,

        "message": (
            "Lab Test is available."
            if lab_test.is_active
            else "Lab Test is currently unavailable."
        )
    }


# =====================================================
# 6. GET LAB TEST BY ID
# =====================================================
@router.get(
    "/{lab_test_id}",
    response_model=LabTestResponse
)
def get_lab_test(
    lab_test_id: int,
    db: Session = Depends(get_db)
):

    lab_test = (
        db.query(LabTest)
        .filter(
            LabTest.id == lab_test_id
        )
        .first()
    )

    if not lab_test:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab Test not found."
        )

    return lab_test


# =====================================================
# 7. UPDATE LAB TEST
# =====================================================
@router.put(
    "/{lab_test_id}",
    response_model=LabTestResponse
)
def update_lab_test(
    lab_test_id: int,
    updated_lab_test: LabTestUpdate,
    db: Session = Depends(get_db)
):

    lab_test_query = (
        db.query(LabTest)
        .filter(
            LabTest.id == lab_test_id
        )
    )

    existing_lab_test = lab_test_query.first()

    if not existing_lab_test:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab Test not found."
        )

    lab_test_query.update(
        updated_lab_test.model_dump()
    )

    db.commit()

    db.refresh(existing_lab_test)

    return existing_lab_test


# =====================================================
# 8. DELETE LAB TEST
# =====================================================
@router.delete(
    "/{lab_test_id}"
)
def delete_lab_test(
    lab_test_id: int,
    db: Session = Depends(get_db)
):

    lab_test_query = (
        db.query(LabTest)
        .filter(
            LabTest.id == lab_test_id
        )
    )

    existing_lab_test = lab_test_query.first()

    if not existing_lab_test:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lab Test not found."
        )

    lab_test_query.delete(
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "Lab Test deleted successfully."
    }

