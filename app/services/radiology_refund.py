from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.radiology_refund import RadiologyRefund


class RefundService:

    def __init__(self, db: Session):
        self.db = db

    # ========================================
    # Create Refund Request
    # Role: Receptionist
    # ========================================
    def create_refund_request(
        self,
        registration_id: int,
        cancellation_reason: str,
        refund_amount: float,
    ):

        refund = RadiologyRefund(

            registration_id=registration_id,

            cancellation_reason=cancellation_reason,

            refund_amount=refund_amount,

            approval_status="Pending",

            refund_status="Pending"
        )

        self.db.add(refund)

        self.db.commit()

        self.db.refresh(refund)

        return refund

    # ========================================
    # Approve Refund
    # Role: Admin / Account Manager
    # ========================================
    def approve_refund(
        self,
        refund_id: int
    ):

        refund = self.get_refund(refund_id)

        if refund.approval_status != "Pending":

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund request already processed."
            )

        refund.approval_status = "Approved"

        self.db.commit()

        self.db.refresh(refund)

        return refund

    # ========================================
    # Reject Refund
    # Role: Admin / Account Manager
    # ========================================
    def reject_refund(
        self,
        refund_id: int
    ):

        refund = self.get_refund(refund_id)

        if refund.approval_status != "Pending":

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund request already processed."
            )

        refund.approval_status = "Rejected"

        refund.refund_status = "Closed"

        self.db.commit()

        self.db.refresh(refund)

        return refund

    # ========================================
    # Process Refund
    # Role: Billing Executive
    # ========================================
    def process_refund(
        self,
        refund_id: int,
        refund_mode: str
    ):

        refund = self.get_refund(refund_id)

        if refund.approval_status != "Approved":

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund is not approved."
            )

        allowed_modes = [
            "Cash",
            "UPI",
            "Card",
            "Bank Transfer"
        ]

        if refund_mode not in allowed_modes:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid refund mode. "
                    "Use Cash, UPI, Card or Bank Transfer."
                )
            )

        refund.refund_mode = refund_mode

        refund.refund_status = "Refunded"

        self.db.commit()

        self.db.refresh(refund)

        return refund

    # ========================================
    # Get All Refunds
    # ========================================
    def get_all_refunds(self):

        return (
            self.db.query(RadiologyRefund)
            .order_by(
                RadiologyRefund.id.desc()
            )
            .all()
        )

    # ========================================
    # Get Refund By ID
    # ========================================
    def get_refund(
        self,
        refund_id: int
    ):

        refund = (
            self.db.query(RadiologyRefund)
            .filter(
                RadiologyRefund.id == refund_id
            )
            .first()
        )

        if not refund:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund request not found."
            )

        return refund

    # ========================================
    # Delete Refund
    # ========================================
    def delete_refund(
        self,
        refund_id: int
    ):

        refund = self.get_refund(refund_id)

        self.db.delete(refund)

        self.db.commit()

        return {
            "message": "Refund deleted successfully."
        }