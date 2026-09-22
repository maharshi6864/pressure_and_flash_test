from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from models.schemas import (
    ProofResponse,
    PressureTestSyncSchema,
    SavePressureTestsRequest,
    FlashTestSyncSchema,
    SaveFlashTestsRequest,
)
from core.database import get_db
from models.db_models import Proof, FlashTest, PressureTest
import json
import os
import shutil
import base64
from datetime import date as dt_date, datetime, timedelta

router = APIRouter(prefix="/sync")

SYNC_API_TOKEN = "super_secure_sync_token_123"

def verify_sync_token(token: str):
    if token != SYNC_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sync token")

@router.get("/flash_server_alive", response_model=List[ProofResponse])
async def flash_server_alive(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    verify_sync_token(token)
    unsynced_proofs = db.query(Proof).filter(
        (Proof.synced_with_flash == False) | (Proof.synced_with_flash == None)
    ).all()

    for proof in unsynced_proofs:
        proof.synced_with_flash = True
    db.commit()

    for proof in unsynced_proofs:
        db.refresh(proof)

    return unsynced_proofs

@router.get("/pressure_server_alive", response_model=List[ProofResponse])
async def pressure_server_alive(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    verify_sync_token(token)
    unsynced_proofs = db.query(Proof).filter(
        (Proof.synced_with_pressure == False) | (Proof.synced_with_pressure == None)
    ).all()

    for proof in unsynced_proofs:
        proof.synced_with_pressure = True
    db.commit()

    for proof in unsynced_proofs:
        db.refresh(proof)

    return unsynced_proofs

@router.post("/save_pressure_test_proof_results")
async def save_pressure_test_proof_results(
    data: Union[SavePressureTestsRequest, List[PressureTestSyncSchema], dict],
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    verify_sync_token(token)

    proof_id: Optional[int] = None
    lot_no: Optional[str] = None
    tests_to_process: List[PressureTestSyncSchema] = []

    if isinstance(data, SavePressureTestsRequest):
        proof_id = data.proof_id or (data.proof_details.id if data.proof_details else None)
        lot_no = data.lot_no or (data.proof_details.lot_no if data.proof_details else None)
        tests_to_process = data.pressure_test_list
    elif isinstance(data, list):
        tests_to_process = data
        if tests_to_process and tests_to_process[0].proof_id:
            proof_id = tests_to_process[0].proof_id
    elif isinstance(data, dict):
        proof_id = data.get("proof_id") or (data.get("proof_details", {}).get("id") if isinstance(data.get("proof_details"), dict) else None)
        lot_no = data.get("lot_no") or (data.get("proof_details", {}).get("lot_no") if isinstance(data.get("proof_details"), dict) else None)
        raw_tests = data.get("pressure_test_list") or data.get("pressure") or data.get("tests") or []
        if isinstance(raw_tests, list):
            tests_to_process = [PressureTestSyncSchema.model_validate(t) for t in raw_tests]
        elif "test_number" in data:
            tests_to_process = [PressureTestSyncSchema.model_validate(data)]

    # Infer proof_id from tests if not specified at root
    if not proof_id:
        for t in tests_to_process:
            if t.proof_id:
                proof_id = t.proof_id
                break

    db_proof = None
    if proof_id:
        db_proof = db.query(Proof).filter(Proof.id == proof_id).first()

    # Fallback lookup by lot_no
    if not db_proof and lot_no:
        db_proof = db.query(Proof).filter(Proof.lot_no == lot_no).first()
        if db_proof:
            proof_id = db_proof.id

    if not db_proof and proof_id:
        raise HTTPException(status_code=404, detail=f"Proof with ID {proof_id} not found")

    saved_count = 0
    for test_item in tests_to_process:
        effective_proof_id = test_item.proof_id or proof_id
        db_test = None

        if test_item.id and effective_proof_id:
            db_test = db.query(PressureTest).filter(
                PressureTest.id == test_item.id,
                PressureTest.proof_id == effective_proof_id
            ).first()

        if not db_test and effective_proof_id and test_item.test_number:
            db_test = db.query(PressureTest).filter(
                PressureTest.proof_id == effective_proof_id,
                PressureTest.test_number == test_item.test_number
            ).first()

        if db_test:
            if test_item.measurement_value is not None:
                db_test.measurement_value = test_item.measurement_value
            if test_item.origin_value is not None:
                db_test.origin_value = test_item.origin_value
            if test_item.mm is not None:
                db_test.mm = test_item.mm
            if test_item.inch is not None:
                db_test.inch = test_item.inch
            if test_item.psi is not None:
                db_test.psi = test_item.psi
            if test_item.mpa is not None:
                db_test.mpa = test_item.mpa
            if test_item.date_time is not None:
                db_test.date_time = test_item.date_time
            if test_item.test_number is not None:
                db_test.test_number = test_item.test_number
        elif effective_proof_id:
            db_test = PressureTest(
                proof_id=effective_proof_id,
                test_number=test_item.test_number,
                measurement_value=test_item.measurement_value,
                origin_value=test_item.origin_value,
                mm=test_item.mm,
                inch=test_item.inch,
                psi=test_item.psi,
                mpa=test_item.mpa,
                date_time=test_item.date_time or datetime.now()
            )
            db.add(db_test)
        saved_count += 1

    if db_proof:
        db_proof.synced_with_pressure = True

    db.commit()

    return {
        "status": "success",
        "proof_id": proof_id,
        "saved_count": saved_count,
        "message": f"Successfully updated all pressure tests for proof {proof_id}"
    }

@router.post("/save_flash_test_proof_results")
async def save_flash_test_proof_results(
    data: Union[SaveFlashTestsRequest, List[FlashTestSyncSchema], dict],
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    verify_sync_token(token)

    proof_id: Optional[int] = None
    lot_no: Optional[str] = None
    tests_to_process: List[FlashTestSyncSchema] = []

    if isinstance(data, SaveFlashTestsRequest):
        proof_id = data.proof_id or (data.proof_details.id if data.proof_details else None)
        lot_no = data.lot_no or (data.proof_details.lot_no if data.proof_details else None)
        tests_to_process = data.flash_test_list
    elif isinstance(data, list):
        tests_to_process = data
        if tests_to_process and tests_to_process[0].proof_id:
            proof_id = tests_to_process[0].proof_id
    elif isinstance(data, dict):
        proof_id = data.get("proof_id") or (data.get("proof_details", {}).get("id") if isinstance(data.get("proof_details"), dict) else None)
        lot_no = data.get("lot_no") or (data.get("proof_details", {}).get("lot_no") if isinstance(data.get("proof_details"), dict) else None)
        raw_tests = data.get("flash_test_list") or data.get("flash") or data.get("flash_tests") or data.get("tests") or []
        if isinstance(raw_tests, list):
            tests_to_process = [FlashTestSyncSchema.model_validate(t) for t in raw_tests]
        elif "test_number" in data:
            tests_to_process = [FlashTestSyncSchema.model_validate(data)]

    # Infer proof_id from tests if not specified at root
    if not proof_id:
        for t in tests_to_process:
            if t.proof_id:
                proof_id = t.proof_id
                break

    db_proof = None
    if proof_id:
        db_proof = db.query(Proof).filter(Proof.id == proof_id).first()

    # Fallback lookup by lot_no
    if not db_proof and lot_no:
        db_proof = db.query(Proof).filter(Proof.lot_no == lot_no).first()
        if db_proof:
            proof_id = db_proof.id

    if not db_proof and proof_id:
        raise HTTPException(status_code=404, detail=f"Proof with ID {proof_id} not found")

    saved_count = 0
    for test_item in tests_to_process:
        effective_proof_id = test_item.proof_id or proof_id
        db_test = None

        if test_item.id and effective_proof_id:
            db_test = db.query(FlashTest).filter(
                FlashTest.id == test_item.id,
                FlashTest.proof_id == effective_proof_id
            ).first()

        if not db_test and effective_proof_id and test_item.test_number:
            db_test = db.query(FlashTest).filter(
                FlashTest.proof_id == effective_proof_id,
                FlashTest.test_number == test_item.test_number
            ).first()

        test_dt = test_item.date_time or test_item.flash_detected_time

        # Process image data (base64)
        saved_image_path = None
        if test_item.image_base64:
            try:
                b64_str = test_item.image_base64
                if "," in b64_str:
                    b64_str = b64_str.split(",", 1)[1]
                img_data = base64.b64decode(b64_str)

                proof_folder = f"proof_{effective_proof_id}" if effective_proof_id else "general"
                upload_dir = os.path.join("uploads", "flash_images", proof_folder)
                os.makedirs(upload_dir, exist_ok=True)

                if test_item.image_filename:
                    img_filename = os.path.basename(test_item.image_filename)
                elif test_item.flash_detected_image_path:
                    img_filename = os.path.basename(test_item.flash_detected_image_path)
                else:
                    img_filename = f"test_{test_item.test_number or 'img'}_{int(datetime.now().timestamp())}.jpg"

                file_path = os.path.join(upload_dir, img_filename)
                with open(file_path, "wb") as f:
                    f.write(img_data)

                saved_image_path = f"/uploads/flash_images/{proof_folder}/{img_filename}"
            except Exception as img_err:
                print(f"[SYNC] Error decoding/saving image for test {test_item.test_number}: {img_err}")

        # Fallback to direct path if no new base64 image was uploaded
        if not saved_image_path and (test_item.flash_detected_image_path or test_item.flash_image_path):
            saved_image_path = test_item.flash_image_path or test_item.flash_detected_image_path

        if db_test:
            if test_item.flash_detected is not None:
                db_test.flash_detected = test_item.flash_detected
            if test_dt is not None:
                db_test.date_time = test_dt
            if test_item.test_number is not None:
                db_test.test_number = test_item.test_number
            if saved_image_path:
                db_test.flash_detected_image_path = saved_image_path
                db_test.flash_image_path = saved_image_path
        elif effective_proof_id:
            db_test = FlashTest(
                proof_id=effective_proof_id,
                test_number=test_item.test_number,
                flash_detected=test_item.flash_detected,
                date_time=test_dt or datetime.now(),
                flash_detected_image_path=saved_image_path,
                flash_image_path=saved_image_path
            )
            db.add(db_test)
        saved_count += 1

    if db_proof:
        db_proof.synced_with_flash = True

    db.commit()

    return {
        "status": "success",
        "proof_id": proof_id,
        "saved_count": saved_count,
        "message": f"Successfully updated all flash tests for proof {proof_id}"
    }