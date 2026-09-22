from typing import Union, List, Optional
from datetime import date as dt_date, datetime as dt_datetime
from sqlalchemy.orm import Session
from models.db_models import Proof, Test
from models.schemas import ProofCreate, SyncFlashRequest


class ProofService:
    def get_all_proofs(self, db: Session):
        return db.query(Proof).order_by(Proof.id.desc()).all()

    def get_proof(self, db: Session, proof_id: int):
        return db.query(Proof).filter(Proof.id == proof_id).first()

    def create_proof(self, db: Session, proof: ProofCreate):
        res = self.add_new_proof(db, proof)
        return self.get_proof(db, res["proof_id"])

    def add_new_proof(self, db: Session, proof_data: Union[SyncFlashRequest, ProofCreate, dict]):
        try:
            # Handle SyncFlashRequest, ProofCreate, or dictionary (e.g. from main server)
            if isinstance(proof_data, SyncFlashRequest):
                p_schema = proof_data.proof
                flash_items = proof_data.flash
            elif isinstance(proof_data, dict):
                if "proof" in proof_data and "flash" in proof_data:
                    p_schema = proof_data["proof"]
                    flash_items = proof_data.get("flash", [])
                elif "proof_details" in proof_data:
                    p_schema = proof_data["proof_details"]
                    flash_items = proof_data.get("flash_test_list", [])
                else:
                    p_schema = proof_data
                    flash_items = proof_data.get("flash_tests", proof_data.get("flash", proof_data.get("tests", [])))
            else:
                p_schema = getattr(proof_data, "proof", proof_data)
                flash_items = (
                    getattr(proof_data, "flash_tests", None)
                    or getattr(proof_data, "flash", None)
                    or getattr(proof_data, "tests", None)
                    or []
                )

            # Extract fields for Proof model
            proof_id = getattr(p_schema, "id", None) if not isinstance(p_schema, dict) else p_schema.get("id")
            lot_no = getattr(p_schema, "lot_no", None) if not isinstance(p_schema, dict) else p_schema.get("lot_no")
            raw_date = getattr(p_schema, "date", None) if not isinstance(p_schema, dict) else p_schema.get("date")
            sample_size = (
                getattr(p_schema, "sample_size", None)
                or getattr(p_schema, "proof_sample_size", None)
                or (p_schema.get("sample_size") if isinstance(p_schema, dict) else None)
                or (p_schema.get("proof_sample_size") if isinstance(p_schema, dict) else None)
                or 10
            )

            if isinstance(raw_date, str):
                try:
                    proof_date = dt_date.fromisoformat(raw_date.split("T")[0])
                except Exception:
                    proof_date = dt_date.today()
            elif isinstance(raw_date, (dt_date, dt_datetime)):
                proof_date = raw_date if isinstance(raw_date, dt_date) else raw_date.date()
            else:
                proof_date = dt_date.today()

            # Check if Proof with this id already exists
            proof_obj = None
            if proof_id:
                proof_obj = db.query(Proof).filter(Proof.id == proof_id).first()

            if not proof_obj and lot_no:
                proof_obj = db.query(Proof).filter(Proof.lot_no == lot_no).first()

            if proof_obj:
                if lot_no:
                    proof_obj.lot_no = lot_no
                if proof_date:
                    proof_obj.date = proof_date
                proof_obj.is_synced = False
                proof_obj.ready_to_sync = False
            else:
                proof_obj = Proof(
                    id=proof_id,
                    lot_no=lot_no or f"LOT-{proof_id or 1}",
                    date=proof_date,
                    is_synced=False,
                    ready_to_sync=False,
                )
                db.add(proof_obj)
                db.flush()

            # Handle tests / flash items
            if flash_items:
                for idx, item in enumerate(flash_items):
                    t_id = getattr(item, "id", None) if not isinstance(item, dict) else item.get("id")
                    t_num = getattr(item, "test_number", None) if not isinstance(item, dict) else item.get("test_number")
                    flash_detected = getattr(item, "flash_detected", None) if not isinstance(item, dict) else item.get("flash_detected")
                    raw_dt = (
                        getattr(item, "date_time", None)
                        or getattr(item, "flash_detected_time", None)
                        or (item.get("date_time") if isinstance(item, dict) else None)
                        or (item.get("flash_detected_time") if isinstance(item, dict) else None)
                    )

                    flash_time = None
                    if isinstance(raw_dt, str):
                        try:
                            flash_time = dt_datetime.fromisoformat(raw_dt)
                        except Exception:
                            flash_time = None
                    elif isinstance(raw_dt, dt_datetime):
                        flash_time = raw_dt

                    test_number = t_num if t_num is not None else (idx + 1)

                    test_obj = None
                    if t_id:
                        test_obj = db.query(Test).filter(Test.id == t_id).first()

                    if not test_obj:
                        test_obj = db.query(Test).filter(
                            Test.proof_id == proof_obj.id,
                            Test.test_number == test_number
                        ).first()

                    if test_obj:
                        test_obj.test_number = test_number
                        if flash_detected is not None:
                            test_obj.flash_detected = flash_detected
                        if flash_time is not None:
                            test_obj.flash_detected_time = flash_time
                    else:
                        test_obj = Test(
                            id=t_id,
                            proof_id=proof_obj.id,
                            test_number=test_number,
                            flash_detected=flash_detected,
                            flash_detected_time=flash_time,
                        )
                        db.add(test_obj)
            else:
                # If no tests provided, ensure tests exist for this proof
                existing_tests = db.query(Test).filter(Test.proof_id == proof_obj.id).all()
                if not existing_tests:
                    num_tests = int(sample_size) if sample_size and int(sample_size) > 0 else 10
                    for i in range(1, num_tests + 1):
                        new_test = Test(
                            proof_id=proof_obj.id,
                            test_number=i,
                            flash_detected=None,
                            flash_detected_time=None
                        )
                        db.add(new_test)

            db.commit()
            db.refresh(proof_obj)

            return {
                "status": True,
                "message": "Proof added successfully",
                "proof_id": proof_obj.id,
            }
        except Exception as e:
            db.rollback()
            raise e


proof_service = ProofService()
