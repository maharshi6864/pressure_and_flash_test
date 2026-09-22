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
    test_number = Column(Integer) # 1 through 10
    flash_detected = Column(Boolean)
    flash_detected_time = Column(DateTime, nullable=True)
    flash_detected_image_path = Column(String,nullable=True)

    proof = relationship("Proof", back_populates="tests")
