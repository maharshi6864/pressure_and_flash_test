from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status
from core.database import get_db
from models.schemas import SyncPressureRequest, DeleteProofRequest
from services.proof_service import proof_service
from services.sync_server import sync_server

router = APIRouter(prefix="/sync")

@router.get("/main_server_alive")
async def main_server_alive(db: Session = Depends(get_db)):
    sync_server.push_all_pending_proofs(db)
    return {
        "status": "ok",
    }

@router.post("/add_new_proof")
async def add_new_proofs(proof: SyncPressureRequest, db: Session = Depends(get_db)):
    try:
        return proof_service.add_new_proof(db, proof)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add new proof: {str(e)}"
        )

@router.delete("/proof/{proof_id}")
async def delete_proof_by_id(
    proof_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return proof_service.delete_proof(db, proof_id=proof_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete proof: {str(e)}"
        )

@router.post("/delete_proof")
async def delete_proof_post(
    request: DeleteProofRequest,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        return proof_service.delete_proof(db, proof_id=request.proof_id, lot_no=request.lot_no)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete proof: {str(e)}"
        )

@router.get("/fetch_unsynced_proofs")
async def fetch_unsynced_proofs():
    return sync_server.inform_main_server_alive()

@router.post("/push_proof_results/{proof_id}")
async def push_proof_results(proof_id: int, db: Session = Depends(get_db)):
    result = sync_server.push_proof_results(db, proof_id)
    if not result.get("status"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error") or result.get("detail") or "Failed to push proof results"
        )
    return result