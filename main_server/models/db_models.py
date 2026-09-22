from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import date, datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=True) # Plain text password for development
    hashed_password = Column(String, nullable=True) # Legacy column
    role = Column(String, default="user") # 'admin' or 'user'
    created_at = Column(DateTime, default=datetime.utcnow)

class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    detonator_type = Column(String, default="356_LZ", index=True)  # "356_LZ", "135_LZY", "RGM"
    lot_no = Column(String, index=True)
    sample_received_on = Column(Date, nullable=True)
    sample_size = Column(Integer, nullable=True, default=10)
    proof_results = Column(String, nullable=True)
    date_of_proof = Column(Date, default=date.today)
    schedule_ref = Column(String, nullable=True)

    # Test Observation & Remarks fields
    drop_test_sample_size = Column(Integer, nullable=True)
    drop_test_date = Column(Date, nullable=True)
    drop_test_obs = Column(String, nullable=True)
    drop_test_remarks = Column(String, nullable=True)

    sensitivity_test_sample_size = Column(Integer, nullable=True)
    sensitivity_test_date = Column(Date, nullable=True)
    sensitivity_test_obs = Column(String, nullable=True)
    sensitivity_test_remarks = Column(String, nullable=True)

    sens_upper_sample_size = Column(Integer, nullable=True)
    sens_upper_date = Column(Date, nullable=True)
    sens_upper_obs = Column(String, nullable=True)
    sens_upper_remarks = Column(String, nullable=True)

    sens_lower_sample_size = Column(Integer, nullable=True)
    sens_lower_date = Column(Date, nullable=True)
    sens_lower_obs = Column(String, nullable=True)
    sens_lower_remarks = Column(String, nullable=True)

    flash_test_sample_size = Column(Integer, nullable=True)
    flash_test_date = Column(Date, nullable=True)
    flash_test_obs = Column(String, nullable=True)
    flash_test_remarks = Column(String, nullable=True)

    pressure_test_sample_size = Column(Integer, nullable=True)
    pressure_test_date = Column(Date, nullable=True)
    pressure_test_obs = Column(String, nullable=True)
    pressure_test_remarks = Column(String, nullable=True)

    # Legacy fields kept for backward compatibility if present in db
    on_line_slip_no = Column(String, nullable=True)
    slip_date = Column(Date, nullable=True)
    type_of_proof = Column(String, nullable=True)
    store = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    schedule_test_programme_ref = Column(String, nullable=True)
    material_used = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    date = Column(Date, default=date.today)
    result_no = Column(String, nullable=True)

    synced_with_pressure = Column(Boolean, nullable=True, default=False)
    synced_with_flash = Column(Boolean, nullable=True, default=False)

    # Relationships
    flash_tests = relationship("FlashTest", back_populates="proof", cascade="all, delete-orphan")
    pressure_tests = relationship("PressureTest", back_populates="proof", cascade="all, delete-orphan")

class FlashTest(Base):
    __tablename__ = "flash_tests"

    id = Column(Integer, primary_key=True, index=True)
    proof_id = Column(Integer, ForeignKey("proofs.id"))
    test_number = Column(Integer) # 1 through 10

    flash_detected = Column(Boolean)

    date_time = Column(DateTime, nullable=True)
    flash_detected_image_path = Column(String, nullable=True)
    flash_image_path = Column(String, nullable=True)
    
    proof = relationship("Proof", back_populates="flash_tests")

class PressureTest(Base):
    __tablename__ = "pressure_tests"

    id = Column(Integer, primary_key=True, index=True)
    proof_id = Column(Integer, ForeignKey("proofs.id"))
    test_number = Column(Integer) # 1 through 10
    
    measurement_value = Column(Float, nullable=True)
    origin_value = Column(Float,nullable=True)
    mm = Column(Float, nullable=True)
    inch = Column(String, nullable=True)
    psi = Column(Float, nullable=True)
    mpa = Column(Float, nullable=True)
    
    date_time = Column(DateTime, nullable=True)

    proof = relationship("Proof", back_populates="pressure_tests")
