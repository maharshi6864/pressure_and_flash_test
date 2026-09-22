from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from core.database import get_db
from models.db_models import Proof, FlashTest, PressureTest, User
from models.schemas import (
    ProofCreate,
    ProofUpdate,
    ProofResponse,
    FlashTestUpdate,
    FlashTestResponse,
    PressureTestUpdate,
    PressureTestResponse,
)
from core.security import get_current_user, get_current_admin
from services.proof_service import proof_service
from services.sync_service import sync_service
from core.lookup_table import get_mpa_from_inch, get_inch_from_mpa


router = APIRouter(prefix="/api/proofs")

@router.post("", response_model=dict)
async def create_proof(
    proof_in: ProofCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        response = await proof_service.add_proof(db, proof_in)
        return response
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[ProofResponse])
async def get_proofs(db: Session = Depends(get_db)):
    return db.query(Proof).order_by(Proof.id.desc()).all()

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_proofs = db.query(Proof).count()
    synced_flash_count = db.query(Proof).filter(Proof.synced_with_flash == True).count()
    synced_pressure_count = db.query(Proof).filter(Proof.synced_with_pressure == True).count()
    
    total_flash_tests = db.query(FlashTest).count()
    flash_detected_count = db.query(FlashTest).filter(FlashTest.flash_detected == True).count()
    
    total_pressure_tests = db.query(PressureTest).count()
    
    pressure_tests_with_mpa = db.query(PressureTest.mpa).filter(PressureTest.mpa != None).all()
    avg_mpa = 0.0
    if pressure_tests_with_mpa:
        mpa_vals = [p[0] for p in pressure_tests_with_mpa if p[0] is not None]
        if mpa_vals:
            avg_mpa = round(sum(mpa_vals) / len(mpa_vals), 2)

    recent_proofs_db = db.query(Proof).order_by(Proof.id.desc()).limit(5).all()
    recent_proofs = [ProofResponse.model_validate(p).model_dump(mode="json") for p in recent_proofs_db]

    return {
        "total_proofs": total_proofs,
        "synced_flash_count": synced_flash_count,
        "synced_pressure_count": synced_pressure_count,
        "total_flash_tests": total_flash_tests,
        "flash_detected_count": flash_detected_count,
        "total_pressure_tests": total_pressure_tests,
        "avg_pressure_mpa": avg_mpa,
        "recent_proofs": recent_proofs
    }

@router.get("/{proof_id}", response_model=ProofResponse)
async def get_proof(proof_id: int, db: Session = Depends(get_db)):
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    return proof

@router.put("/{proof_id}", response_model=ProofResponse)
async def update_proof(
    proof_id: int,
    proof_in: ProofUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")

    update_data = proof_in.model_dump(exclude_unset=True)
    flash_tests_data = update_data.pop("flash_tests", None)
    pressure_tests_data = update_data.pop("pressure_tests", None)

    for field, value in update_data.items():
        if hasattr(proof, field):
            setattr(proof, field, value)

    if flash_tests_data:
        for ft_item in flash_tests_data:
            ft_id = ft_item.get("id")
            db_ft = None
            if ft_id:
                db_ft = db.query(FlashTest).filter(FlashTest.id == ft_id, FlashTest.proof_id == proof_id).first()
            if not db_ft and ft_item.get("test_number"):
                db_ft = db.query(FlashTest).filter(FlashTest.test_number == ft_item["test_number"], FlashTest.proof_id == proof_id).first()
            if db_ft:
                for k, v in ft_item.items():
                    if k != "id" and v is not None and hasattr(db_ft, k):
                        setattr(db_ft, k, v)

    if pressure_tests_data:
        for pt_item in pressure_tests_data:
            pt_id = pt_item.get("id")
            db_pt = None
            if pt_id:
                db_pt = db.query(PressureTest).filter(PressureTest.id == pt_id, PressureTest.proof_id == proof_id).first()
            if not db_pt and pt_item.get("test_number"):
                db_pt = db.query(PressureTest).filter(PressureTest.test_number == pt_item["test_number"], PressureTest.proof_id == proof_id).first()
            if db_pt:
                for k, v in pt_item.items():
                    if k != "id" and v is not None and hasattr(db_pt, k):
                        setattr(db_pt, k, v)

    db.commit()
    db.refresh(proof)
    try:
        await sync_service.sync_proof_by_id(proof.id)
    except Exception as e:
        print(f"[SYNC] Notice on sync after proof update: {e}")
    return proof

@router.delete("/{proof_id}")
async def delete_proof(
    proof_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")

    lot_no = proof.lot_no

    # 1. Inform child nodes to delete tests and proof
    node_results = await sync_service.delete_proof_from_nodes(proof_id, lot_no=lot_no)

    # 2. Clean up any physical uploaded images for this proof
    proof_upload_dir = os.path.join("uploads", "flash_images", f"proof_{proof_id}")
    if os.path.exists(proof_upload_dir):
        try:
            shutil.rmtree(proof_upload_dir, ignore_errors=True)
        except Exception as e:
            print(f"[CLEANUP] Error removing proof image folder {proof_upload_dir}: {e}")

    # 3. Delete proof from database (cascades to flash_tests and pressure_tests)
    db.delete(proof)
    db.commit()

    return {
        "status": "success",
        "message": f"Proof {proof_id} (Lot {lot_no}) and all associated test records were deleted successfully.",
        "nodes_notified": node_results
    }

@router.put("/{proof_id}/flash-tests/{test_id}", response_model=FlashTestResponse)
async def update_flash_test(
    proof_id: int,
    test_id: int,
    test_in: FlashTestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(FlashTest).filter(FlashTest.id == test_id, FlashTest.proof_id == proof_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Flash test not found")

    update_data = test_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "flash_detected_time" and value is not None and not update_data.get("date_time"):
            test.date_time = value
        elif hasattr(test, field) and value is not None:
            setattr(test, field, value)

    db.commit()
    db.refresh(test)
    try:
        await sync_service.sync_proof_by_id(proof_id)
    except Exception as e:
        print(f"[SYNC] Notice on sync after flash test update: {e}")
    return test

@router.put("/{proof_id}/pressure-tests/{test_id}", response_model=PressureTestResponse)
async def update_pressure_test(
    proof_id: int,
    test_id: int,
    test_in: PressureTestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    test = db.query(PressureTest).filter(PressureTest.id == test_id, PressureTest.proof_id == proof_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Pressure test not found")

    update_data = test_in.model_dump(exclude_unset=True)

    # Auto-map inch <-> mpa if one is provided
    if "inch" in update_data and update_data["inch"] and ("mpa" not in update_data or update_data["mpa"] is None):
        mapped_mpa = get_mpa_from_inch(update_data["inch"])
        if mapped_mpa is not None:
            update_data["mpa"] = mapped_mpa
    elif "mpa" in update_data and update_data["mpa"] is not None and ("inch" not in update_data or not update_data["inch"]):
        mapped_inch = get_inch_from_mpa(update_data["mpa"])
        if mapped_inch:
            update_data["inch"] = mapped_inch

    for field, value in update_data.items():
        if field == "psi":
            continue  # PSI is no longer stored
        if hasattr(test, field) and value is not None:
            setattr(test, field, value)

    db.commit()
    db.refresh(test)
    try:
        await sync_service.sync_proof_by_id(proof_id)
    except Exception as e:
        print(f"[SYNC] Notice on sync after pressure test update: {e}")
    return test

@router.get("/{proof_id}/tests")
async def get_proof_tests(proof_id: int, db: Session = Depends(get_db)):
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    return {
        "flash_tests": proof.flash_tests,
        "pressure_tests": proof.pressure_tests
    }

@router.post("/sync/trigger")
async def trigger_sync(
    current_user: User = Depends(get_current_user)
):
    result = await sync_service.inform_servers_alive_status()
    return {"status": "success", "result": result}

