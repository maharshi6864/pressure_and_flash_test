from pydantic import BaseModel
from typing import List, Optional
from datetime import date as dt_date, datetime as dt_datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class UserResponse(UserBase):
    id: int
    password: Optional[str] = None
    created_at: Optional[dt_datetime] = None
    class Config:
        from_attributes = True

# Proof Base Schema
class ProofBase(BaseModel):
    detonator_type: Optional[str] = "356_LZ"  # "356_LZ", "135_LZY", "RGM"
    lot_no: str
    sample_received_on: Optional[dt_date] = None
    sample_size: Optional[int] = 10
    proof_results: Optional[str] = None
    date_of_proof: Optional[dt_date] = None
    schedule_ref: Optional[str] = None

    # Test Observations and Remarks
    drop_test_sample_size: Optional[int] = None
    drop_test_date: Optional[dt_date] = None
    drop_test_obs: Optional[str] = None
    drop_test_remarks: Optional[str] = None

    sensitivity_test_sample_size: Optional[int] = None
    sensitivity_test_date: Optional[dt_date] = None
    sensitivity_test_obs: Optional[str] = None
    sensitivity_test_remarks: Optional[str] = None

    sens_upper_sample_size: Optional[int] = None
    sens_upper_date: Optional[dt_date] = None
    sens_upper_obs: Optional[str] = None
    sens_upper_remarks: Optional[str] = None

    sens_lower_sample_size: Optional[int] = None
    sens_lower_date: Optional[dt_date] = None
    sens_lower_obs: Optional[str] = None
    sens_lower_remarks: Optional[str] = None

    flash_test_sample_size: Optional[int] = None
    flash_test_date: Optional[dt_date] = None
    flash_test_obs: Optional[str] = None
    flash_test_remarks: Optional[str] = None

    pressure_test_sample_size: Optional[int] = None
    pressure_test_date: Optional[dt_date] = None
    pressure_test_obs: Optional[str] = None
    pressure_test_remarks: Optional[str] = None

    # Compatibility fields
    on_line_slip_no: Optional[str] = None
    slip_date: Optional[dt_date] = None
    type_of_proof: Optional[str] = None
    store: Optional[str] = None
    quantity: Optional[int] = None
    schedule_test_programme_ref: Optional[str] = None
    material_used: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[dt_date] = None
    result_no: Optional[str] = None

class ProofCreate(ProofBase):
    pass

class FlashTestBase(BaseModel):
    test_number: Optional[int] = None
    flash_detected: Optional[bool] = None
    date_time: Optional[dt_datetime] = None
    flash_detected_time: Optional[dt_datetime] = None
    flash_image_path: Optional[str] = None
    flash_detected_image_path: Optional[str] = None
    flash_detection_image_path: Optional[str] = None

class FlashTestCreate(FlashTestBase):
    pass

class FlashTestUpdate(BaseModel):
    id: Optional[int] = None
    test_number: Optional[int] = None
    flash_detected: Optional[bool] = None
    date_time: Optional[dt_datetime] = None
    flash_detected_time: Optional[dt_datetime] = None
    flash_image_path: Optional[str] = None
    flash_detected_image_path: Optional[str] = None
    flash_detection_image_path: Optional[str] = None

class FlashTestResponse(FlashTestBase):
    id: int
    proof_id: int
    class Config:
        from_attributes = True



class PressureTestBase(BaseModel):
    test_number: Optional[int] = None
    measurement_value: Optional[float] = None
    origin_value: Optional[float] = None
    mm: Optional[float] = None
    inch: Optional[str] = None
    psi: Optional[float] = None
    mpa: Optional[float] = None
    date_time: Optional[dt_datetime] = None
    datetime: Optional[dt_datetime] = None

class PressureTestCreate(PressureTestBase):
    pass

class PressureTestUpdate(BaseModel):
    id: Optional[int] = None
    test_number: Optional[int] = None
    measurement_value: Optional[float] = None
    origin_value: Optional[float] = None
    mm: Optional[float] = None
    inch: Optional[str] = None
    psi: Optional[float] = None
    mpa: Optional[float] = None
    date_time: Optional[dt_datetime] = None

class PressureTestResponse(PressureTestBase):
    id: int
    proof_id: int
    class Config:
        from_attributes = True



class ProofResponse(ProofBase):
    id: int
    synced_with_pressure: Optional[bool] = False
    synced_with_flash: Optional[bool] = False
    flash_tests: List[FlashTestResponse] = []
    pressure_tests: List[PressureTestResponse] = []
    
    class Config:
        from_attributes = True


class ProofUpdate(BaseModel):
    detonator_type: Optional[str] = None
    lot_no: Optional[str] = None
    sample_received_on: Optional[dt_date] = None
    sample_size: Optional[int] = None
    proof_results: Optional[str] = None
    date_of_proof: Optional[dt_date] = None
    schedule_ref: Optional[str] = None

    drop_test_sample_size: Optional[int] = None
    drop_test_date: Optional[dt_date] = None
    drop_test_obs: Optional[str] = None
    drop_test_remarks: Optional[str] = None

    sensitivity_test_sample_size: Optional[int] = None
    sensitivity_test_date: Optional[dt_date] = None
    sensitivity_test_obs: Optional[str] = None
    sensitivity_test_remarks: Optional[str] = None

    sens_upper_sample_size: Optional[int] = None
    sens_upper_date: Optional[dt_date] = None
    sens_upper_obs: Optional[str] = None
    sens_upper_remarks: Optional[str] = None

    sens_lower_sample_size: Optional[int] = None
    sens_lower_date: Optional[dt_date] = None
    sens_lower_obs: Optional[str] = None
    sens_lower_remarks: Optional[str] = None

    flash_test_sample_size: Optional[int] = None
    flash_test_date: Optional[dt_date] = None
    flash_test_obs: Optional[str] = None
    flash_test_remarks: Optional[str] = None

    pressure_test_sample_size: Optional[int] = None
    pressure_test_date: Optional[dt_date] = None
    pressure_test_obs: Optional[str] = None
    pressure_test_remarks: Optional[str] = None

    # Legacy fields
    on_line_slip_no: Optional[str] = None
    slip_date: Optional[dt_date] = None
    type_of_proof: Optional[str] = None
    store: Optional[str] = None
    quantity: Optional[int] = None
    schedule_test_programme_ref: Optional[str] = None
    material_used: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[dt_date] = None
    result_no: Optional[str] = None
    flash_tests: Optional[List[FlashTestUpdate]] = None
    pressure_tests: Optional[List[PressureTestUpdate]] = None



class SyncFlashData(BaseModel):
    proof: ProofCreate
    tests: List[FlashTestCreate]

class SyncPressureData(BaseModel):
    proof: ProofCreate
    tests: List[PressureTestCreate]



class ProofSyncSchema(BaseModel):
    id: int
    detonator_type: Optional[str] = None
    lot_no: str
    sample_received_on: Optional[dt_date] = None
    sample_size: Optional[int] = None
    proof_results: Optional[str] = None
    date_of_proof: Optional[dt_date] = None
    schedule_ref: Optional[str] = None

    drop_test_sample_size: Optional[int] = None
    drop_test_date: Optional[dt_date] = None
    drop_test_obs: Optional[str] = None
    drop_test_remarks: Optional[str] = None

    sensitivity_test_sample_size: Optional[int] = None
    sensitivity_test_date: Optional[dt_date] = None
    sensitivity_test_obs: Optional[str] = None
    sensitivity_test_remarks: Optional[str] = None

    sens_upper_sample_size: Optional[int] = None
    sens_upper_date: Optional[dt_date] = None
    sens_upper_obs: Optional[str] = None
    sens_upper_remarks: Optional[str] = None

    sens_lower_sample_size: Optional[int] = None
    sens_lower_date: Optional[dt_date] = None
    sens_lower_obs: Optional[str] = None
    sens_lower_remarks: Optional[str] = None

    flash_test_sample_size: Optional[int] = None
    flash_test_date: Optional[dt_date] = None
    flash_test_obs: Optional[str] = None
    flash_test_remarks: Optional[str] = None

    pressure_test_sample_size: Optional[int] = None
    pressure_test_date: Optional[dt_date] = None
    pressure_test_obs: Optional[str] = None
    pressure_test_remarks: Optional[str] = None

    on_line_slip_no: Optional[str] = None
    slip_date: Optional[dt_date] = None
    type_of_proof: Optional[str] = None
    store: Optional[str] = None
    quantity: Optional[int] = None
    schedule_test_programme_ref: Optional[str] = None
    material_used: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[dt_date] = None
    result_no: Optional[str] = None

    class Config:
        from_attributes = True

class FlashTestSyncSchema(BaseModel):
    id: Optional[int] = None
    proof_id: Optional[int] = None
    test_number: Optional[int] = None
    flash_detected: Optional[bool] = None
    date_time: Optional[dt_datetime] = None
    flash_detected_time: Optional[dt_datetime] = None
    flash_detected_image_path: Optional[str] = None
    flash_image_path: Optional[str] = None
    flash_detection_image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_filename: Optional[str] = None

    class Config:
        from_attributes = True

class PressureTestSyncSchema(BaseModel):
    id: Optional[int] = None
    proof_id: Optional[int] = None
    test_number: Optional[int] = None
    measurement_value: Optional[float] = None
    origin_value: Optional[float] = None
    mm: Optional[float] = None
    inch: Optional[str] = None
    psi: Optional[float] = None
    mpa: Optional[float] = None
    date_time: Optional[dt_datetime] = None

    class Config:
        from_attributes = True

class SavePressureTestsRequest(BaseModel):
    proof_id: Optional[int] = None
    lot_no: Optional[str] = None
    proof_details: Optional[ProofSyncSchema] = None
    pressure_test_list: List[PressureTestSyncSchema] = []

class SaveFlashTestsRequest(BaseModel):
    proof_id: Optional[int] = None
    lot_no: Optional[str] = None
    proof_details: Optional[ProofSyncSchema] = None
    flash_test_list: List[FlashTestSyncSchema] = []

class DashboardStatsResponse(BaseModel):
    total_proofs: int = 0
    synced_flash_count: int = 0
    synced_pressure_count: int = 0
    total_flash_tests: int = 0
    total_pressure_tests: int = 0
    flash_detected_count: int = 0
    avg_pressure_mpa: Optional[float] = 0.0
    recent_proofs: List[ProofResponse] = []