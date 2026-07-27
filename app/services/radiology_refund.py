from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_refund import RadiologyRefund


class RadiologyRefundService:

    def __init__(self, db: Session):
        self.db = db

    # --------------------------------
    # Create Radiology Refund
    # --------------------------------
    def create_refund(
        self,
        registration_id: int,
        refund_amount: float,
        refund_reason: str,
        remarks: str | None,
    ):

        # --------------------------------
        # Validate Refund Amount
        # --------------------------------
        if refund_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount must be greater than zero."
            )

        # --------------------------------
        # Create Radiology Refund
        # --------------------------------
        refund = RadiologyRefund(
            registration_id=registration_id,
            refund_amount=refund_amount,
            refund_reason=refund_reason,
            status="Pending",
            remarks=remarks,
        )

        self.db.add(refund)

        self.db.commit()

        self.db.refresh(refund)

        return refund

    # --------------------------------
    # Get All Radiology Refunds
    # --------------------------------
    def get_all_refunds(self):

        return (
            self.db.query(
                RadiologyRefund
            )
            .order_by(
                RadiologyRefund.id.desc()
            )
            .all()
        )

    # --------------------------------
    # Get Radiology Refund By ID
    # --------------------------------
    def get_refund(
        self,
        refund_id: int
    ):

        refund = (
            self.db.query(
                RadiologyRefund
            )
            .filter(
                RadiologyRefund.id == refund_id
            )
            .first()
        )

        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Radiology refund not found."
            )

        return refund

    # --------------------------------
    # Update Radiology Refund
    # --------------------------------
    def update_refund(
        self,
        refund_id: int,
        refund_amount: float | None,
        refund_reason: str | None,
        status_value: str | None,
        remarks: str | None,
    ):

        # --------------------------------
        # Find Refund
        # --------------------------------
        refund = self.get_refund(
            refund_id
        )

        # --------------------------------
        # Validate Refund Amount
        # --------------------------------
        if (
            refund_amount is not None
            and refund_amount <= 0
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount must be greater than zero."
            )

        # --------------------------------
        # Update Refund Amount
        # --------------------------------
        if refund_amount is not None:
            refund.refund_amount = refund_amount

        # --------------------------------
        # Update Refund Reason
        # --------------------------------
        if refund_reason is not None:
            refund.refund_reason = refund_reason

        # --------------------------------
        # Update Refund Status
        # --------------------------------
        if status_value is not None:

            allowed_statuses = [
                "Pending",
                "Approved",
                "Rejected",
                "Completed",
            ]

            if status_value not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Invalid refund status. "
                        "Allowed statuses are: "
                        "Pending, Approved, Rejected, Completed."
                    )
                )

            refund.status = status_value

        # --------------------------------
        # Update Remarks
        # --------------------------------
        if remarks is not None:
            refund.remarks = remarks

        # --------------------------------
        # Save Changes
        # --------------------------------
        self.db.commit()

        self.db.refresh(refund)

        return refund

    # --------------------------------
    # Delete Radiology Refund
    # --------------------------------
    def delete_refund(
        self,
        refund_id: int
    ):

        # --------------------------------
        # Find Refund
        # --------------------------------
        refund = self.get_refund(
            refund_id
        )

        # --------------------------------
        # Delete Refund
        # --------------------------------
        self.db.delete(refund)

        self.db.commit()

        return {
            "message": "Radiology refund deleted successfully."
        }