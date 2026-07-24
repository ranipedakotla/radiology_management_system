from app.db.session import SessionLocal
from app.models.blood_bank import Donor
from app.task.blood_bank_notification import check_donor_eligibility
from app.utils.email import send_email


def notify_eligible_donors():
    db = SessionLocal()

    donors = db.query(Donor).all()

    for donor in donors:
        is_eligible, reason = check_donor_eligibility(donor)

        if is_eligible:
            send_email(
                subject="Eligible for Blood Donation",
                recipients=[donor.email],
                body=f"""
                Hello {donor.name},


                You are now eligible to donate blood.

                Please visit the blood bank when convenient.


                Thank you.
                """
            )
        else:
            send_email(
                subject="Blood Donation Eligibility Update",
                recipients=[donor.email],
                body=f"""
                Hello {donor.name},


                You are currently not eligible to donate blood.

                Reason: <b>{reason}</b>


                Please try again later.
                """
            )

    db.close()
