from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from core.database import get_db
from models.schemas import SyncFlashRequest
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