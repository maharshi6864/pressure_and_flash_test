from typing import Union, List, Optional
from datetime import date as dt_date, datetime as dt_datetime
from sqlalchemy.orm import Session
from models.db_models import Proof, Test
from models.schemas import ProofCreate, SyncPressureRequest


class ProofService:
    def get_all_proofs(self, db: Session):
        return db.query(Proof).order_by(Proof.id.desc()).all()

    def get_proof(self, db: Session, proof_id: int):
        return db.query(Proof).filter(Proof.id == proof_id).first()

    def add_new_proof(self, db: Session, proof_data: Union[SyncPressureRequest, ProofCreate, dict]):
        try:
            # Handle SyncPressureRequest, ProofCreate, or dictionary (e.g. from main server)
            if isinstance(proof_data, SyncPressureRequest):
                p_schema = proof_data.proof
                pressure_items = proof_data.pressure
            elif isinstance(proof_data, dict):
                if "proof" in proof_data and "pressure" in proof_data:
                    p_schema = proof_data["proof"]
                    pressure_items = proof_data.get("pressure", [])
                elif "proof_details" in proof_data:
                    p_schema = proof_data["proof_details"]
                    pressure_items = proof_data.get("pressure_test_list", [])
                else:
                    p_schema = proof_data
                    pressure_items = proof_data.get("pressure_tests", proof_data.get("pressure", proof_data.get("tests", [])))
            else:
                p_schema = getattr(proof_data, "proof", proof_data)
                pressure_items = (
                    getattr(proof_data, "pressure_tests", None)
                    or getattr(proof_data, "pressure", None)
                    or getattr(proof_data, "tests", None)
                    or []
                )

            # Extract fields for Proof model
            proof_id = getattr(p_schema, "id", None) if not isinstance(p_schema, dict) else p_schema.get("id")
            lot_no = getattr(p_schema, "lot_no", None) if not isinstance(p_schema, dict) else p_schema.get("lot_no")
            raw_date = getattr(p_schema, "date", None) if not isinstance(p_schema, dict) else p_schema.get("date")

            if isinstance(raw_date, str):
                try:
                    proof_date = dt_date.fromisoformat(raw_date.split("T")[0])
                except Exception:
                    proof_date = dt_date.today()
            elif isinstance(raw_date, dt_date):
                proof_date = raw_date
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

            # Handle tests / pressure items
            if pressure_items:
                for item in pressure_items:
                    t_id = getattr(item, "id", None) if not isinstance(item, dict) else item.get("id")
                    t_num = getattr(item, "test_number", None) if not isinstance(item, dict) else item.get("test_number")
                    t_meas = getattr(item, "measurement_value", None) if not isinstance(item, dict) else item.get("measurement_value")
                    t_orig = getattr(item, "origin_value", None) if not isinstance(item, dict) else item.get("origin_value")
                    
                    t_mm = (
                        getattr(item, "mm", None) or getattr(item, "max_mm", None)
                        if not isinstance(item, dict)
                        else (item.get("mm") or item.get("max_mm"))
                    )
                    t_inch = (
                        getattr(item, "inch", None) or getattr(item, "max_inch", None)
                        if not isinstance(item, dict)
                        else (item.get("inch") or item.get("max_inch"))
                    )
                    t_psi = (
                        getattr(item, "psi", None) or getattr(item, "max_psi", None)
                        if not isinstance(item, dict)
                        else (item.get("psi") or item.get("max_psi"))
                    )
                    t_mpa = (
                        getattr(item, "mpa", None) or getattr(item, "max_mpa", None)
                        if not isinstance(item, dict)
                        else (item.get("mpa") or item.get("max_mpa"))
                    )
                    raw_dt = (
                        getattr(item, "date_time", None) or getattr(item, "datetime", None)
                        if not isinstance(item, dict)
                        else (item.get("date_time") or item.get("datetime"))
                    )
                    if isinstance(raw_dt, str):
                        try:
                            t_dt = dt_datetime.fromisoformat(raw_dt)
                        except Exception:
                            t_dt = None
                    else:
                        t_dt = raw_dt

                    # Look up existing test by ID or by (proof_id, test_number)
                    test_obj = None
                    if t_id:
                        test_obj = db.query(Test).filter(Test.id == t_id).first()
                    if not test_obj and t_num is not None:
                        test_obj = db.query(Test).filter(Test.proof_id == proof_obj.id, Test.test_number == t_num).first()

                    if test_obj:
                        test_obj.proof_id = proof_obj.id
                        if t_num is not None:
                            test_obj.test_number = t_num
                        test_obj.measurement_value = t_meas
                        test_obj.origin_value = t_orig
                        test_obj.mm = t_mm
                        test_obj.inch = t_inch
                        test_obj.psi = t_psi
                        test_obj.mpa = t_mpa
                        test_obj.datetime = t_dt
                    else:
                        new_test = Test(
                            id=t_id,
                            proof_id=proof_obj.id,
                            test_number=t_num or 1,
                            measurement_value=t_meas,
                            origin_value=t_orig,
                            mm=t_mm,
                            inch=t_inch,
                            psi=t_psi,
                            mpa=t_mpa,
                            datetime=t_dt,
                        )
                        db.add(new_test)
            else:
                existing_tests_count = db.query(Test).filter(Test.proof_id == proof_obj.id).count()
                if existing_tests_count == 0:
                    sample_size = getattr(p_schema, "sample_size", 10) if not isinstance(p_schema, dict) else p_schema.get("sample_size", 10)
                    total_tests = sample_size if sample_size and sample_size > 0 else 10
                    for i in range(1, total_tests + 1):
                        new_test = Test(
                            proof_id=proof_obj.id,
                            test_number=i,
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
