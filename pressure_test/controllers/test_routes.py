from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from core.database import get_db
from models.schemas import MarkerSizeConfig, ProofResponse, TestResponse
from repositories.current_objects import current_objects
from services.camera_service import camera_service, mjpeg_frame_generator
from services.measurement_service import measurement_service
from services.proof_service import proof_service
from services.test_service import test_service

router = APIRouter()

@router.get("/video_feed/test")
async def video_feed_test():
    return StreamingResponse(
        mjpeg_frame_generator(camera_service, processor=measurement_service.process_frame),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/api/test/set_origin")
async def set_origin():
    if hasattr(measurement_service, '_last_current_x'):
        measurement_service.set_origin(measurement_service._last_current_x)
        return {"status": "success"}
    return {"status": "error", "message": "No marker detected yet"}

@router.get("/api/test/reset")
async def reset_values():
    current_objects.reset()
    measurement_service.max_positive_x = 0.0
    return {"status": "success"}

@router.get("/api/proofs", response_model=List[ProofResponse])
async def get_all_proofs(db: Session = Depends(get_db)):
    return proof_service.get_all_proofs(db)

@router.get("/api/proofs/{proof_id}", response_model=ProofResponse)
async def get_proof(proof_id: int, db: Session = Depends(get_db)):
    proof = proof_service.get_proof(db, proof_id)
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    return proof

@router.get("/api/proofs/{proof_id}/tests", response_model=List[TestResponse])
async def get_tests_for_proof(proof_id: int, db: Session = Depends(get_db)):
    return test_service.get_tests_for_proof(db, proof_id)

@router.get("/api/proofs/{proof_id}/tests/{test_id}", response_model=TestResponse)
async def set_current_test_id(proof_id: int, test_id: int, db: Session = Depends(get_db)):
    test = test_service.set_current_test_id(db, proof_id, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

class MeasurementUpdate(BaseModel):
    value: float

@router.post("/api/tests/{test_id}/measurement")
async def save_test_measurement(test_id: int, update: MeasurementUpdate, db: Session = Depends(get_db)):
    test = test_service.update_test_measurement(db, test_id, update.value)
    if test:
        return {"status": "success", "measurement_value": test.measurement_value}
    return {"status": "error", "message": "Test not found"}
