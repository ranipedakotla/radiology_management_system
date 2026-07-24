from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

# Customize prefixes and sequence width here
PREFIX_PATIENT = "PAT"   # or "USD" if you prefer that style
PREFIX_DOCTOR  = "DOC"
PREFIX_STAFF   = "STF"
SEQ_WIDTH = 3            # e.g., 3 -> ...001, 2 -> ...01


def next_code(db: Session, prefix: str, when: Optional[datetime] = None, width: int = SEQ_WIDTH) -> str:
    """
    Generates a unique code like PREFIXYYYYMM### using a monthly counter per prefix.
    Safe under concurrency (row lock on upsert).
    """
    when = when or datetime.utcnow()
    yyyymm = when.strftime("%Y%m")

    # Upsert row; increment counter atomically on duplicate
    upsert = text("""
        INSERT INTO id_sequences (name, yyyymm, counter)
        VALUES (:n, :m, 1)
        ON DUPLICATE KEY UPDATE counter = counter + 1
    """)
    db.execute(upsert, {"n": prefix, "m": yyyymm})

    # Read the current counter value after increment/insert
    sel = text("SELECT counter FROM id_sequences WHERE name = :n AND yyyymm = :m")
    seq = db.execute(sel, {"n": prefix, "m": yyyymm}).scalar()
    seq = int(seq or 1)

    return f"{prefix}{yyyymm}{seq:0{width}d}"
