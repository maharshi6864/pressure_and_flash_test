from pydantic import BaseModel, computed_field
from typing import Optional, List
from datetime import date as dt_date, datetime as dt_datetime

class CameraConfig(BaseModel):
    source: str

class MarkerSizeConfig(BaseModel):
    marker_size: float # in meters

class TestBase(BaseModel):
    test_number: int
    measurement_value: Optional[float] = None
    origin_value: Optional[float] = None
    mm: Optional[float] = None
    inch: Optional[str] = None
    psi: Optional[float] = None
    mpa: Optional[float] = None
    datetime: Optional[dt_datetime] = None

class TestCreate(TestBase):
    pass

class TestResponse(TestBase):
    id: int
    proof_id: int

    @computed_field
    @property
    def max_mpa(self) -> Optional[float]:
        return self.mpa

    @computed_field
    @property
    def max_psi(self) -> Optional[float]:
        return self.psi

    @computed_field
    @property
    def max_mm(self) -> Optional[float]:
        return self.mm

    @computed_field
    @property
    def max_inch(self) -> Optional[str]:
        return self.inch

    class Config:
        from_attributes = True

class ProofBase(BaseModel):
    lot_no: str
    date: Optional[dt_date] = None
    is_synced: Optional[bool] = False
    ready_to_sync: Optional[bool] = False
    synced_at: Optional[dt_datetime] = None

class ProofCreate(ProofBase):
    tests: Optional[List[TestCreate]] = None

class ProofResponse(ProofBase):
    id: int
    tests: List[TestResponse] = []

    class Config:
        from_attributes = True

class PressureTestSyncSchema(BaseModel):
    id: int
    proof_id: int
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

class SyncPressureRequest(BaseModel):
    proof: ProofSyncSchema
    pressure: List[PressureTestSyncSchema] = []

class DeleteProofRequest(BaseModel):
    proof_id: Optional[int] = None
    lot_no: Optional[str] = None