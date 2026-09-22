from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import date

class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    lot_no = Column(String, index=True)
    
    date = Column(Date, default=date.today)

    is_synced = Column(Boolean, default=False)
    ready_to_sync = Column(Boolean, default=False)
    synced_at = Column(DateTime, nullable=True)

    tests = relationship("Test", back_populates="proof", cascade="all, delete-orphan")

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    proof_id = Column(Integer, ForeignKey("proofs.id"))

    test_number = Column(Integer) # 1 to 10

    measurement_value = Column(Float, nullable=True)
    origin_value = Column(Float,nullable=True) 

    mm = Column(Float, nullable=True)
    inch = Column(String, nullable=True)
    psi = Column(Float, nullable=True)
    mpa = Column(Float, nullable=True)
    
    datetime = Column(DateTime, nullable=True)

    proof = relationship("Proof", back_populates="tests")
