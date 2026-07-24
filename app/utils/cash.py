from fastapi import HTTPException

def ensure_non_negative(*nums: int | None):
    for n in nums:
        if n is not None and n < 0:
            raise HTTPException(status_code=400, detail="cash denomination counts cannot be negative")

def sum_cash(den500=0, den200=0, den100=0, den50=0, den20=0, den10=0) -> int:
    return (
        (den500 or 0) * 500
        + (den200 or 0) * 200
        + (den100 or 0) * 100
        + (den50 or 0) * 50
        + (den20 or 0) * 20
        + (den10 or 0) * 10
    )
