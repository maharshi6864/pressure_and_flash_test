from fastapi import Query
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from services.camera_service import camera_service, mjpeg_frame_generator
from services.test_service import test_service
from models.schemas import MarkerSizeConfig, TestResponse
from core.database import get_db
from services.detect_flash_service import detect_flash_service
from repositories.current_objects import CurrentObjects

router = APIRouter()

@router.get("/video_feed/test")
async def video_feed_test():
    return StreamingResponse(
        mjpeg_frame_generator(camera_service,processor=detect_flash_service.process_frame),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/api/proofs/{proof_id}/tests", response_model=List[TestResponse])
async def get_tests_for_proof(proof_id: int, db: Session = Depends(get_db)):
    return test_service.get_tests_for_proof(db, proof_id)

@router.get("/api/test/setCurrentTestId")
async def set_current_test_id(test_id: int,db: Session = Depends(get_db)):
    test_id = test_service.set_current_test_id(db, test_id)
    if test_id:
        return {"status": "success", "test_id": test_id}
    return {"status": "error", "message": "Test not found"}

@router.post("/api/test/reset")
def reset_test():
    test_service.reset_test_info()
    return {"status": "success"}

@router.get("/api/test/get_ready_status")
def get_ready_status():
    ready = CurrentObjects.ready_status
    return {"status": "success", "ready_status": ready}

@router.get("/api/test/set_ready_status")
def set_ready_status(ready: bool):
    CurrentObjects.ready_status = ready
    return {"status": "success"}

@router.post("/api/test/end_manually")
def end_test_manually(db: Session = Depends(get_db)):
    test_id = CurrentObjects.current_test_id
    if not test_id:
        return {"status": "error", "message": "No test selected"}
    test = test_service.end_test_manually(db, test_id)
    if test:
        return {"status": "success", "flash_detected": False, "flash_duration_ms": None}
    return {"status": "error", "message": "Test not found"}

@router.post("/api/tests/{test_id}/save")
def save_test(test_id: int, db: Session = Depends(get_db)):
    test = test_service.save_test_result(db, test_id)
    if test:
        return {
            "status": "success", 
            "flash_detected": test.flash_detected, 
        }
    return {"status": "error", "message": "Test not found"}

