from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from models.schemas import ProofCreate, ProofResponse
from services.proof_service import proof_service
from typing import List

router = APIRouter(prefix="/api")

@router.get("/proofs", response_model=List[ProofResponse])
async def get_proofs(db: Session = Depends(get_db)):
    return proof_service.get_all_proofs(db)

@router.post("/proofs", response_model=ProofResponse)
async def create_proof(proof: ProofCreate, db: Session = Depends(get_db)):
    return proof_service.create_proof(db, proof)
