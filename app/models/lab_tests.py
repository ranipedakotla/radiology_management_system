from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from app.db.base import Base


class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    test_type = Column(String(100), nullable=False)
    test_sub_type = Column(String(150), nullable=False)
    cost = Column(Float, nullable=False)
    body_part = Column(String(100), nullable=False)
    precautions = Column(Text, nullable=True)
    id_proof_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)