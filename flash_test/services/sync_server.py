from datetime import datetime
import threading
import requests
import base64
import os
from sqlalchemy.orm import Session
from core.config import settings
from core.database import SessionLocal
from models.db_models import Proof, Test
from services.proof_service import proof_service


class SyncServer:
    def inform_main_server_alive(self):
        url = f"http://{settings.MAIN_SERVER_HOST}:{settings.MAIN_SERVER_PORT}/sync/flash_server_alive"
        try:
            response = requests.get(
                url,
                params={"token": settings.SYNC_API_TOKEN},
                timeout=5.0
            )
            if response.status_code == 200:
                proofs = response.json()
                if isinstance(proofs, list):
                    db = SessionLocal()
                    try:
                        for proof_data in proofs:
                            proof_service.add_new_proof(db, proof_data)
                        print(f"[SYNC] Successfully fetched and synced {len(proofs)} unsynced proofs from main server.")
                    finally:
                        db.close()

                # Also push any local pending completed proofs
                db = SessionLocal()
                try:
                    self.push_all_pending_proofs(db)
                finally:
                    db.close()

                return {"status": True, "count": len(proofs) if isinstance(proofs, list) else 0}
            else:
                print(f"[SYNC] Main server returned status {response.status_code}: {response.text}")
                return {"status": False, "status_code": response.status_code}
        except Exception as e:
            print(f"[SYNC] Failed to inform main server or fetch unsynced proofs: {e}")
            return {"status": False, "error": str(e)}

    def push_proof_results(self, db: Session, proof_id: int):
        proof = db.query(Proof).filter(Proof.id == proof_id).first()
        if not proof:
            return {"status": False, "error": f"Proof with ID {proof_id} not found"}

        tests = db.query(Test).filter(Test.proof_id == proof_id).order_by(Test.test_number).all()

        flash_test_list = []
        for t in tests:
            image_b64 = None
            image_filename = None
            if t.flash_detected_image_path and os.path.exists(t.flash_detected_image_path):
                try:
                    with open(t.flash_detected_image_path, "rb") as img_f:
                        image_b64 = base64.b64encode(img_f.read()).decode("utf-8")
                    image_filename = os.path.basename(t.flash_detected_image_path)
                except Exception as e:
                    print(f"[SYNC] Error reading image for test {t.id}: {e}")

            flash_test_list.append({
                "id": t.id,
                "proof_id": t.proof_id,
                "test_number": t.test_number,
                "flash_detected": t.flash_detected,
                "date_time": t.flash_detected_time.isoformat() if t.flash_detected_time else None,
                "flash_detected_time": t.flash_detected_time.isoformat() if t.flash_detected_time else None,
                "flash_detected_image_path": t.flash_detected_image_path,
                "image_base64": image_b64,
                "image_filename": image_filename
            })

        payload = {
            "proof_id": proof.id,
            "lot_no": proof.lot_no,
            "flash_test_list": flash_test_list
        }

        url = f"http://{settings.MAIN_SERVER_HOST}:{settings.MAIN_SERVER_PORT}/sync/save_flash_test_proof_results"
        try:
            response = requests.post(
                url,
                params={"token": settings.SYNC_API_TOKEN},
                json=payload,
                timeout=15.0
            )
            if response.status_code == 200:
                proof.is_synced = True
                proof.synced_at = datetime.now()
                db.commit()
                db.refresh(proof)
                print(f"[SYNC] Successfully pushed flash results for proof {proof.id} to main server.")
                return {"status": True, "data": response.json()}
            else:
                print(f"[SYNC] Main server returned status {response.status_code}: {response.text}")
                return {"status": False, "status_code": response.status_code, "detail": response.text}
        except Exception as e:
            print(f"[SYNC] Failed to push proof results to main server: {e}")
            return {"status": False, "error": str(e)}

    def push_all_pending_proofs(self, db: Session):
        pending_proofs = db.query(Proof).filter(
            Proof.ready_to_sync == True,
            (Proof.is_synced == False) | (Proof.is_synced == None)
        ).all()

        results = []
        for p in pending_proofs:
            res = self.push_proof_results(db, p.id)
            results.append({"proof_id": p.id, "result": res})
        return results


sync_server = SyncServer()