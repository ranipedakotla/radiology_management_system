from datetime import date


def check_donor_eligibility(donor):
    if donor.age < 18:
        return False, "Age must be at least 18 years"

    if donor.last_donation_date:
        days_gap = (date.today() - donor.last_donation_date).days
        if days_gap < 90:
            return False, f"Minimum 90 days gap required ({days_gap} days completed)"

    return True, None
