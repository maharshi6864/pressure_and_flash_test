from services.counter_service import counter_service
from sqlalchemy.orm import Session
from models.db_models import Test, Proof
from repositories.current_objects import CurrentObjects
from datetime import datetime
import os
import cv2
from core.config import settings
from services.sync_server import sync_server


class TestService:
    def get_tests_for_proof(self, db: Session, proof_id: int):
        return db.query(Test).filter(Test.proof_id == proof_id).order_by(Test.test_number).all()

    def set_current_test_id(self, db: Session, test_id: int):
        test = db.query(Test).filter(Test.id == test_id).first()
        if test is None:
            return None
        CurrentObjects.current_test_id = test.id
        return test.id

    def reset_test_info(self):
        CurrentObjects.current_test_id = None
        CurrentObjects.flash_detection_image = None
        CurrentObjects.flash_image = None
        CurrentObjects.flash_detection = False
        CurrentObjects.flash_detected_time = None

    def save_test_result(self, db: Session, test_id: int):
        test = db.query(Test).filter(Test.id == test_id).first()
        if test is None:
            return None

        test.flash_detected = CurrentObjects.flash_detection
        test.flash_detected_time = CurrentObjects.flash_detected_time or datetime.now()

        # Save image of test (flash image or latest frame for no flash)
        image_to_save = CurrentObjects.flash_image
        if image_to_save is None:
            image_to_save = CurrentObjects.latest_display_frame if CurrentObjects.latest_display_frame is not None else CurrentObjects.latest_frame

        if image_to_save is not None:
            proof = db.query(Proof).filter(Proof.id == test.proof_id).first()
            raw_lot = proof.lot_no if proof and proof.lot_no else f"proof_{test.proof_id}"
            lot_name = "".join(c for c in raw_lot if c.isalnum() or c in ('-', '_')).strip() or f"proof_{test.proof_id}"
            
            dt = test.flash_detected_time or datetime.now()
            ts_str = dt.strftime("%Y%m%d_%H%M%S")
            
            folder = os.path.join(settings.FLASH_IMAGES_DIR, lot_name)
            os.makedirs(folder, exist_ok=True)
            
            filename = f"test_{test.test_number}_{ts_str}.jpg"
            file_path = os.path.join(folder, filename)
            
            try:
                cv2.imwrite(file_path, image_to_save)
                test.flash_detected_image_path = file_path
                print(f"[IMAGE] Test image saved: {file_path}")
            except Exception as e:
                print(f"[IMAGE] Error saving test image: {e}")
        else:
            test.flash_detected_image_path = None

        self.reset_test_info()

        # Check if all tests for this proof are completed
        all_tests = db.query(Test).filter(Test.proof_id == test.proof_id).all()
        proof = None
        if all_tests and all(t.flash_detected is not None for t in all_tests):
            proof = db.query(Proof).filter(Proof.id == test.proof_id).first()
            if proof:
                proof.ready_to_sync = True
                sync_server.push_proof_results(db, proof.id)

        db.commit()
        db.refresh(test)

        return test

    def end_test_manually(self, db: Session, test_id: int):
        test = db.query(Test).filter(Test.id == test_id).first()
        if test is None:
            return None

        # Update test in database
        test.flash_detected = False
        test.flash_detected_time = datetime.now()

        image_to_save = CurrentObjects.latest_display_frame if CurrentObjects.latest_display_frame is not None else CurrentObjects.latest_frame
        if image_to_save is not None:
            proof = db.query(Proof).filter(Proof.id == test.proof_id).first()
            raw_lot = proof.lot_no if proof and proof.lot_no else f"proof_{test.proof_id}"
            lot_name = "".join(c for c in raw_lot if c.isalnum() or c in ('-', '_')).strip() or f"proof_{test.proof_id}"
            
            dt = test.flash_detected_time or datetime.now()
            ts_str = dt.strftime("%Y%m%d_%H%M%S")
            
            folder = os.path.join(settings.FLASH_IMAGES_DIR, lot_name)
            os.makedirs(folder, exist_ok=True)
            
            filename = f"test_{test.test_number}_{ts_str}.jpg"
            file_path = os.path.join(folder, filename)
            
            try:
                cv2.imwrite(file_path, image_to_save)
                test.flash_detected_image_path = file_path
                print(f"[IMAGE] Manual end test image saved: {file_path}")
            except Exception as e:
                print(f"[IMAGE] Error saving test image: {e}")
        else:
            test.flash_detected_image_path = None

        self.reset_test_info()

        # Check if all tests for this proof are completed
        all_tests = db.query(Test).filter(Test.proof_id == test.proof_id).all()
        proof = None
        if all_tests and all(t.flash_detected is not None for t in all_tests):
            proof = db.query(Proof).filter(Proof.id == test.proof_id).first()
            if proof:
                proof.ready_to_sync = True
                sync_server.push_proof_results(db, proof.id)

        db.commit()
        db.refresh(test)

        return test



test_service = TestService()
