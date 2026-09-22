from models.db_models import Proof
from models.db_models import PressureTest
from models.db_models import FlashTest
from models.schemas import ProofSyncSchema, PressureTestSyncSchema, FlashTestSyncSchema
from services.sync_service import sync_service


class ProofService:


    async def add_proof(self, db, proof_in):
        db_pressure_test_list = []
        db_flash_test_list = []

        proof_data = proof_in.model_dump()
        det_type = proof_data.get("detonator_type") or "356_LZ"
        proof_data["detonator_type"] = det_type

        # Apply specific defaults
        if det_type == "356_LZ":
            if not proof_data.get("schedule_ref"):
                proof_data["schedule_ref"] = "CQA/Proof Schedule/Det/1/11"
            if proof_data.get("drop_test_sample_size") is None:
                proof_data["drop_test_sample_size"] = 20
            if proof_data.get("sensitivity_test_sample_size") is None:
                proof_data["sensitivity_test_sample_size"] = 10
            if proof_data.get("flash_test_sample_size") is None:
                proof_data["flash_test_sample_size"] = 10
            if proof_data.get("pressure_test_sample_size") is None:
                proof_data["pressure_test_sample_size"] = 10

        # Populate compatibility fields if not explicitly provided
        if not proof_data.get("date") and proof_data.get("date_of_proof"):
            proof_data["date"] = proof_data["date_of_proof"]
        if not proof_data.get("result_no") and proof_data.get("proof_results"):
            proof_data["result_no"] = proof_data["proof_results"]
        if not proof_data.get("schedule_test_programme_ref") and proof_data.get("schedule_ref"):
            proof_data["schedule_test_programme_ref"] = proof_data["schedule_ref"]
        if not proof_data.get("slip_date") and proof_data.get("sample_received_on"):
            proof_data["slip_date"] = proof_data["sample_received_on"]

        db_proof = Proof(**proof_data)
        db.add(db_proof)
        db.commit()
        db.refresh(db_proof)

        # Calculate number of Pressure and Flash tests based on user-provided sample sizes
        # For pressure tests: whatever user passes for pressure_test_sample_size, or fallback
        pressure_count = db_proof.pressure_test_sample_size
        if pressure_count is None:
            if det_type in ["356_LZ", "135_LZY", "RGM"]:
                pressure_count = db_proof.sample_size or 10
            else:
                pressure_count = 0

        # For flash tests: whatever user passes for flash_test_sample_size (only detonator types that support flash tests)
        flash_count = db_proof.flash_test_sample_size
        if flash_count is None:
            if det_type == "356_LZ":
                flash_count = db_proof.sample_size or 10
            else:
                flash_count = 0

        if pressure_count and pressure_count > 0:
            for i in range(pressure_count):
                pt = PressureTest(proof_id=db_proof.id, test_number=i + 1)
                db.add(pt)
                db_pressure_test_list.append(pt)

        if flash_count and flash_count > 0:
            for i in range(flash_count):
                ft = FlashTest(proof_id=db_proof.id, test_number=i + 1)
                db.add(ft)
                db_flash_test_list.append(ft)

        # Commit all tests together
        db.commit()

        for item in db_pressure_test_list:
            db.refresh(item)

        for item in db_flash_test_list:
            db.refresh(item)

        request = {
            "proof_details": ProofSyncSchema.model_validate(db_proof).model_dump(mode='json'),
            "pressure_test_list": [PressureTestSyncSchema.model_validate(item).model_dump(mode='json') for item in db_pressure_test_list],
            "flash_test_list": [FlashTestSyncSchema.model_validate(item).model_dump(mode='json') for item in db_flash_test_list],
        }

        sync_status = await sync_service.inform_servers_new_proof(request)

        db_proof.synced_with_pressure = sync_status.get("synced_with_pressure", False)
        db_proof.synced_with_flash = sync_status.get("synced_with_flash", False)
        db.commit()
        db.refresh(db_proof)

        return request





proof_service = ProofService()