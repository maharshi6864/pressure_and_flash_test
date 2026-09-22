from repositories.current_objects import current_objects
from sqlalchemy.orm import Session
from models.db_models import Test, Proof


class TestService:
    def get_tests_for_proof(self, db: Session, proof_id: int):
        current_objects.current_proof_id = proof_id
        return db.query(Test).filter(Test.proof_id == proof_id).order_by(Test.test_number).all()

    def update_test_measurement(self, db: Session, test_id: int, value: float):
        from controllers.socket_routes import get_lookup_data
        from services.measurement_service import measurement_service
        from services.sync_server import sync_server
        from datetime import datetime

        current_objects.current_test_id = test_id
        
        test = db.query(Test).filter(Test.id == test_id).first()
        if test:
            test.measurement_value = value
            test.datetime = datetime.now()
            test.origin_value = measurement_service.origin_x

            max_x = current_objects.latest_maximum_x
            if max_x is None:
                max_x = value if value is not None else 0.0

            max_mm = max_x * 1000
            max_lookup = get_lookup_data(max_x)
            test.mm = max_mm
            test.inch = max_lookup.get("inch", "0 inch")
            test.psi = max_lookup.get("psi", 0.0)
            test.mpa = max_lookup.get("mpa", 0.0)

            db.commit()
            db.refresh(test)

            # Check if all tests for this proof are completed
            all_tests = db.query(Test).filter(Test.proof_id == test.proof_id).all()
            if all_tests and all(t.measurement_value is not None for t in all_tests):
                proof = db.query(Proof).filter(Proof.id == test.proof_id).first()
                if proof:
                    proof.ready_to_sync = True
                    db.commit()
                    # Push proof result to the main server immediately
                    sync_server.push_proof_results(db, proof.id)

        return test

    def set_current_test_id(self, db: Session, proof_id: int, test_id: int):
        current_objects.current_proof_id = proof_id
        current_objects.current_test_id = test_id
        return db.query(Test).filter(Test.id == test_id).first()


test_service = TestService()
