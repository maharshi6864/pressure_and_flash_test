from sqlalchemy.orm import Session
from models.db_models import Proof, Test
from core.database import SessionLocal
from datetime import datetime, timedelta

def run_retention_cleanup():
    db: Session = SessionLocal()
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        # Find proofs that are synced and older than 30 days
        old_proofs = db.query(Proof).filter(
            Proof.is_synced == True,
            Proof.date < thirty_days_ago.date()
        ).all()
        
        for proof in old_proofs:
            # Delete from DB
            db.delete(proof)
            
        db.commit()
    except Exception as e:
        print(f"Error during pressure retention cleanup: {e}")
    finally:
        db.close()
