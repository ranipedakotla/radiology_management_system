# from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
# from sqlalchemy.orm import relationship
# from app.db.base import Base
#
# class Hospital(Base):
#     __tablename__ = "hospitals"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String(225))
#     is_active = Column(Boolean, default=True)
#     branches = relationship(
#         "HospitalBranch",
#         back_populates="hospital",
#         lazy="selectin",
#         cascade="all, delete-orphan",
#     )
#
#
#
# class HospitalBranch(Base):
#         __tablename__ = "hospital_branches"
#
#         id = Column(Integer, primary_key=True, index=True)
#         hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
#         branch_name = Column(String(225), nullable=False)
#         location = Column(String(225))
#         contact_number = Column(String(50))
#
#         hospital = relationship("Hospital", back_populates="branches")
