# from sqlite3 import Date
# from sqlalchemy import Column, Integer, String,Date
# from app.database import Base
# from sqlalchemy.orm import relationship


# class Medicine(Base):
#     __tablename__ = "medicines"
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     strength = Column(String(255))
#     dosage_form = Column(String(100))
#     medicine_name = Column(String(255), nullable=False, unique=True)
#     batch_no = Column(String(100))
#     mfg_date = Column(Date)
#     expire_date = Column(Date)
#     quantity = Column(Integer)
#     company = Column(String, nullable=True)
#     Description = Column(String(255))
#     Drug_formula = Column(String(255))
#     purchase_orders = relationship("PurchaseOrder", back_populates="medicine")