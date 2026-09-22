from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status
from core.database import get_db
from core.config import settings
from models.schemas import SyncFlashRequest, DeleteProofRequest
from services.proof_service import proof_service

router = APIRouter(prefix="/sync")

@router.get("/main_server_alive")
async def main_server_alive():
    return {
        "status": "ok",
    }

@router.post("/add_new_proof")
async def add_new_proofs(proof: SyncFlashRequest, db: Session = Depends(get_db)):
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
    if token and token != settings.SYNC_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sync API token"
        )
    try:
        return proof_service.delete_proof(db, proof_id=proof_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete proof: {str(e)}"
        )

@router.post("/delete_proof")
async def sync_delete_proof(
    request: DeleteProofRequest, 
    token: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    if token and token != settings.SYNC_API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sync API token"
        )
    try:
        return proof_service.delete_proof(db, proof_id=request.proof_id, lot_no=request.lot_no)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete proof: {str(e)}"
        )