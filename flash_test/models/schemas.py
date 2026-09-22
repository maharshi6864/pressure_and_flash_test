from pydantic import BaseModel
from typing import Optional, List
from datetime import date as dt_date, datetime as dt_datetime


class CameraConfig(BaseModel):
    source: str


class MarkerSizeConfig(BaseModel):
    marker_size: float # in meters


class TestBase(BaseModel):
    test_number: int
    flash_detected: Optional[bool] = None
    flash_image_path: Optional[str] = None
    flash_detection_image_path: Optional[str] = None
    flash_detected_image_path: Optional[str] = None
    flash_detected_time: Optional[dt_datetime] = None


class TestResponse(TestBase):
    id: int
    proof_id: int

    class Config:
        from_attributes = True


class ProofBase(BaseModel):
    on_line_proof_slip_no: Optional[str] = None
    slip_date: Optional[dt_date] = None
    type_of_proof: Optional[str] = None
    store: Optional[str] = None
    lot_no: str
    quantity: Optional[int] = None
    proof_sample_size: Optional[int] = None
    proof_schedule_test_programme_ref: Optional[str] = None
    material_used: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[dt_date] = None
    proof_result_no: Optional[str] = None
    is_synced: Optional[bool] = False
    ready_to_sync: Optional[bool] = False
    synced_at: Optional[dt_datetime] = None


class ProofCreate(ProofBase):
    pass


class ProofResponse(ProofBase):
    id: int
    tests: List[TestResponse] = []

    class Config:
        from_attributes = True


class ProofSyncSchema(BaseModel):
    id: int
    on_line_slip_no: Optional[str] = None
    slip_date: Optional[dt_date] = None
    type_of_proof: Optional[str] = None
    store: Optional[str] = None
    lot_no: str
    quantity: Optional[int] = None
    sample_size: Optional[int] = None
    schedule_test_programme_ref: Optional[str] = None
    material_used: Optional[str] = None
    remarks: Optional[str] = None
    date: Optional[dt_date] = None
    result_no: Optional[str] = None

    class Config:
        from_attributes = True


class FlashTestSyncSchema(BaseModel):
    id: Optional[int] = None
    proof_id: int
    test_number: Optional[int] = None
    flash_detected: Optional[bool] = None
    date_time: Optional[dt_datetime] = None
    flash_detected_time: Optional[dt_datetime] = None
    flash_detected_image_path: Optional[str] = None
    image_base64: Optional[str] = None
    image_filename: Optional[str] = None

    class Config:
        from_attributes = True


class SyncFlashRequest(BaseModel):
    proof: ProofSyncSchema
    flash: List[FlashTestSyncSchema] = []
