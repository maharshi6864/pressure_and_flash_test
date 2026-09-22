import httpx
import asyncio
from datetime import date as dt_date, datetime as dt_datetime
from core.config import Settings
from core.database import SessionLocal
from models.db_models import Proof
from models.schemas import ProofSyncSchema, PressureTestSyncSchema, FlashTestSyncSchema


class SyncService:

    def _get_target_urls(self, base_url: str):
        """Return candidate URLs to handle localhost / 127.0.0.1 differences."""
        urls = [base_url]
        if "localhost" in base_url:
            urls.append(base_url.replace("localhost", "127.0.0.1"))
        elif "127.0.0.1" in base_url:
            urls.append(base_url.replace("127.0.0.1", "localhost"))
        return urls

    def _format_proof_dict(self, proof_data: dict, target_type: str = "pressure") -> dict:
        """Ensure all fields required by child node ProofSyncSchema are populated."""
        p_id = proof_data.get("id")
        date_val = str(
            proof_data.get("date_of_proof")
            or proof_data.get("date")
            or dt_date.today().isoformat()
        )
        result_val = str(proof_data.get("proof_results") or proof_data.get("result_no") or "")
        sched_val = str(proof_data.get("schedule_ref") or proof_data.get("schedule_test_programme_ref") or "")
        slip_date_val = str(proof_data.get("sample_received_on") or proof_data.get("slip_date") or date_val)

        if target_type == "pressure":
            sample_size_val = (
                proof_data.get("pressure_test_sample_size")
                or proof_data.get("sample_size")
                or 10
            )
        else:
            sample_size_val = (
                proof_data.get("flash_test_sample_size")
                or proof_data.get("sample_size")
                or 10
            )

        return {
            "id": p_id,
            "lot_no": proof_data.get("lot_no") or f"LOT-{p_id}",
            "date": date_val,
            "sample_size": sample_size_val,
            "schedule_test_programme_ref": sched_val,
            "result_no": result_val,
            "slip_date": slip_date_val,
            "type_of_proof": proof_data.get("type_of_proof") or proof_data.get("detonator_type") or "356_LZ",
            "store": proof_data.get("store") or "Store",
            "quantity": proof_data.get("quantity") or sample_size_val,
            "material_used": proof_data.get("material_used") or "[]",
            "remarks": proof_data.get("remarks") or "",
            "on_line_slip_no": proof_data.get("on_line_slip_no") or f"SLIP-{p_id}",
        }

    def _format_pressure_tests(self, tests: list, proof_id: int) -> list:
        formatted = []
        for idx, t in enumerate(tests):
            t_id = t.get("id") if isinstance(t, dict) else getattr(t, "id", None)
            t_num = (t.get("test_number") if isinstance(t, dict) else getattr(t, "test_number", None)) or (idx + 1)
            t_meas = t.get("measurement_value") if isinstance(t, dict) else getattr(t, "measurement_value", None)
            t_orig = t.get("origin_value") if isinstance(t, dict) else getattr(t, "origin_value", None)
            t_mm = t.get("mm") if isinstance(t, dict) else getattr(t, "mm", None)
            t_inch = t.get("inch") if isinstance(t, dict) else getattr(t, "inch", None)
            t_psi = t.get("psi") if isinstance(t, dict) else getattr(t, "psi", None)
            t_mpa = t.get("mpa") if isinstance(t, dict) else getattr(t, "mpa", None)
            raw_dt = t.get("date_time") if isinstance(t, dict) else getattr(t, "date_time", None)

            dt_val = None
            if raw_dt:
                dt_val = raw_dt.isoformat() if hasattr(raw_dt, "isoformat") else str(raw_dt)

            formatted.append({
                "id": t_id,
                "proof_id": proof_id,
                "test_number": t_num,
                "measurement_value": t_meas,
                "origin_value": t_orig,
                "mm": t_mm,
                "inch": t_inch,
                "psi": t_psi,
                "mpa": t_mpa,
                "date_time": dt_val,
            })
        return formatted

    def _format_flash_tests(self, tests: list, proof_id: int) -> list:
        formatted = []
        for idx, t in enumerate(tests):
            t_id = t.get("id") if isinstance(t, dict) else getattr(t, "id", None)
            t_num = (t.get("test_number") if isinstance(t, dict) else getattr(t, "test_number", None)) or (idx + 1)
            flash_det = t.get("flash_detected") if isinstance(t, dict) else getattr(t, "flash_detected", None)
            raw_dt = (
                (t.get("date_time") if isinstance(t, dict) else getattr(t, "date_time", None))
                or (t.get("flash_detected_time") if isinstance(t, dict) else getattr(t, "flash_detected_time", None))
            )
            img_path = (
                (t.get("flash_detected_image_path") if isinstance(t, dict) else getattr(t, "flash_detected_image_path", None))
                or (t.get("flash_image_path") if isinstance(t, dict) else getattr(t, "flash_image_path", None))
            )

            dt_val = None
            if raw_dt:
                dt_val = raw_dt.isoformat() if hasattr(raw_dt, "isoformat") else str(raw_dt)

            formatted.append({
                "id": t_id,
                "proof_id": proof_id,
                "test_number": t_num,
                "flash_detected": flash_det,
                "date_time": dt_val,
                "flash_detected_time": dt_val,
                "flash_detected_image_path": img_path,
            })
        return formatted

    async def inform_servers_alive_status(self):
        pressure_connected = False
        flash_connected = False

        async with httpx.AsyncClient(timeout=4.0) as async_client:
            # 1. Notify Pressure Test Server
            for url in self._get_target_urls(Settings.pressure_test_server_url):
                try:
                    pressure_res = await async_client.get(
                        f'{url}/sync/main_server_alive',
                        params={"token": Settings.SYNC_API_TOKEN}
                    )
                    if 200 <= pressure_res.status_code < 300:
                        pressure_connected = True
                        print(f"[SYNC] Pressure server acknowledged alive at {url}")
                        break
                except Exception as e:
                    pass

            # 2. Notify Flash Test Server
            for url in self._get_target_urls(Settings.flash_test_server_url):
                try:
                    flash_res = await async_client.get(
                        f'{url}/sync/main_server_alive',
                        params={"token": Settings.SYNC_API_TOKEN}
                    )
                    if 200 <= flash_res.status_code < 300:
                        flash_connected = True
                        print(f"[SYNC] Flash server acknowledged alive at {url}")
                        break
                except Exception as e:
                    pass

        # 3. Push all pending unsynced proofs created while child servers were down/offline
        await self.sync_all_unsynced_proofs()

        return {
            "pressure_connected": pressure_connected,
            "flash_connected": flash_connected
        }

    async def inform_servers_new_proof(self, proof: dict):
        synced_with_pressure = False
        synced_with_flash = False

        proof_details = proof.get('proof_details', {})
        proof_id = proof_details.get('id')
        pressure_tests_raw = proof.get('pressure_test_list', [])
        flash_tests_raw = proof.get('flash_test_list', [])

        has_pressure_tests = bool(pressure_tests_raw)
        has_flash_tests = bool(flash_tests_raw)

        # Prepare formatted payloads for nodes
        pressure_proof_dict = self._format_proof_dict(proof_details, "pressure")
        flash_proof_dict = self._format_proof_dict(proof_details, "flash")
        pressure_tests = self._format_pressure_tests(pressure_tests_raw, proof_id)
        flash_tests = self._format_flash_tests(flash_tests_raw, proof_id)

        async with httpx.AsyncClient(timeout=5.0) as async_client:
            # Sync with Pressure Test Server if proof has pressure tests
            if has_pressure_tests:
                for url in self._get_target_urls(Settings.pressure_test_server_url):
                    try:
                        res = await async_client.post(
                            f'{url}/sync/add_new_proof',
                            params={"token": Settings.SYNC_API_TOKEN},
                            json={
                                "proof": pressure_proof_dict,
                                "pressure": pressure_tests,
                            },
                        )
                        if 200 <= res.status_code < 300:
                            synced_with_pressure = True
                            print(f"[SYNC] Successfully informed Pressure server ({url}) for proof {proof_id}")
                            break
                        else:
                            print(f"[SYNC] Pressure server at {url} returned {res.status_code}: {res.text}")
                    except Exception as e:
                        print(f"[SYNC] Error reaching Pressure server at {url}: {e}")
            else:
                synced_with_pressure = True

            # Sync with Flash Test Server if proof has flash tests
            if has_flash_tests:
                for url in self._get_target_urls(Settings.flash_test_server_url):
                    try:
                        res = await async_client.post(
                            f'{url}/sync/add_new_proof',
                            params={"token": Settings.SYNC_API_TOKEN},
                            json={
                                "proof": flash_proof_dict,
                                "flash": flash_tests,
                            },
                        )
                        if 200 <= res.status_code < 300:
                            synced_with_flash = True
                            print(f"[SYNC] Successfully informed Flash server ({url}) for proof {proof_id}")
                            break
                        else:
                            print(f"[SYNC] Flash server at {url} returned {res.status_code}: {res.text}")
                    except Exception as e:
                        print(f"[SYNC] Error reaching Flash server at {url}: {e}")
            else:
                synced_with_flash = True

        return {
            "synced_with_pressure": synced_with_pressure,
            "synced_with_flash": synced_with_flash
        }

    async def sync_proof_by_id(self, proof_id: int):
        """Fetch proof from database and push to child servers."""
        db = SessionLocal()
        try:
            p = db.query(Proof).filter(Proof.id == proof_id).first()
            if not p:
                return {"synced_with_pressure": False, "synced_with_flash": False}

            req = {
                "proof_details": ProofSyncSchema.model_validate(p).model_dump(mode='json'),
                "pressure_test_list": [PressureTestSyncSchema.model_validate(item).model_dump(mode='json') for item in p.pressure_tests],
                "flash_test_list": [FlashTestSyncSchema.model_validate(item).model_dump(mode='json') for item in p.flash_tests],
            }
            sync_status = await self.inform_servers_new_proof(req)
            if sync_status.get("synced_with_pressure"):
                p.synced_with_pressure = True
            if sync_status.get("synced_with_flash"):
                p.synced_with_flash = True
            db.commit()
            return sync_status
        except Exception as e:
            print(f"[SYNC] Error in sync_proof_by_id for proof {proof_id}: {e}")
            return {"synced_with_pressure": False, "synced_with_flash": False}
        finally:
            db.close()

    async def sync_all_unsynced_proofs(self):
        """Query DB for any unsynced proofs and push them to child nodes."""
        db = SessionLocal()
        try:
            unsynced_proofs = db.query(Proof).filter(
                (Proof.synced_with_pressure == False) | (Proof.synced_with_flash == False) |
                (Proof.synced_with_pressure == None) | (Proof.synced_with_flash == None)
            ).all()

            if unsynced_proofs:
                print(f"[SYNC] Found {len(unsynced_proofs)} unsynced proofs to push to nodes...")

            for p in unsynced_proofs:
                req = {
                    "proof_details": ProofSyncSchema.model_validate(p).model_dump(mode='json'),
                    "pressure_test_list": [PressureTestSyncSchema.model_validate(item).model_dump(mode='json') for item in p.pressure_tests],
                    "flash_test_list": [FlashTestSyncSchema.model_validate(item).model_dump(mode='json') for item in p.flash_tests],
                }
                sync_status = await self.inform_servers_new_proof(req)
                if sync_status.get("synced_with_pressure"):
                    p.synced_with_pressure = True
                if sync_status.get("synced_with_flash"):
                    p.synced_with_flash = True
            db.commit()
        except Exception as e:
            print(f"[SYNC] Error syncing pending proofs to child servers: {e}")
        finally:
            db.close()

    async def periodic_sync_worker(self):
        """Background loop that periodically syncs any unsynced proofs to child servers."""
        print("[SYNC] Starting background periodic sync worker (interval: 10s)...")
        while True:
            try:
                await asyncio.sleep(10)
                await self.sync_all_unsynced_proofs()
            except asyncio.CancelledError:
                print("[SYNC] Periodic sync worker stopped.")
                break
            except Exception as e:
                print(f"[SYNC] Periodic sync worker iteration notice: {e}")


    async def delete_proof_from_nodes(self, proof_id: int, lot_no: str = None):
        """Notify child nodes (Pressure & Flash servers) to delete the proof and all associated tests."""
        pressure_deleted = False
        flash_deleted = False

        async with httpx.AsyncClient(timeout=5.0) as async_client:
            # 1. Notify Pressure Test Server
            for url in self._get_target_urls(Settings.pressure_test_server_url):
                try:
                    # Attempt DELETE endpoint first
                    res = await async_client.delete(
                        f'{url}/sync/proof/{proof_id}',
                        params={"token": Settings.SYNC_API_TOKEN}
                    )
                    if 200 <= res.status_code < 300:
                        pressure_deleted = True
                        print(f"[SYNC] Pressure server at {url} deleted proof {proof_id}")
                        break
                    elif res.status_code in [404, 405]:
                        # Fallback to POST delete_proof
                        res2 = await async_client.post(
                            f'{url}/sync/delete_proof',
                            params={"token": Settings.SYNC_API_TOKEN},
                            json={"proof_id": proof_id, "lot_no": lot_no}
                        )
                        if 200 <= res2.status_code < 300:
                            pressure_deleted = True
                            print(f"[SYNC] Pressure server at {url} acknowledged delete_proof for {proof_id}")
                            break
                    else:
                        print(f"[SYNC] Pressure server at {url} delete response status {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"[SYNC] Error notifying Pressure server at {url} to delete proof {proof_id}: {e}")

            # 2. Notify Flash Test Server
            for url in self._get_target_urls(Settings.flash_test_server_url):
                try:
                    # Attempt DELETE endpoint first
                    res = await async_client.delete(
                        f'{url}/sync/proof/{proof_id}',
                        params={"token": Settings.SYNC_API_TOKEN}
                    )
                    if 200 <= res.status_code < 300:
                        flash_deleted = True
                        print(f"[SYNC] Flash server at {url} deleted proof {proof_id}")
                        break
                    elif res.status_code in [404, 405]:
                        # Fallback to POST delete_proof
                        res2 = await async_client.post(
                            f'{url}/sync/delete_proof',
                            params={"token": Settings.SYNC_API_TOKEN},
                            json={"proof_id": proof_id, "lot_no": lot_no}
                        )
                        if 200 <= res2.status_code < 300:
                            flash_deleted = True
                            print(f"[SYNC] Flash server at {url} acknowledged delete_proof for {proof_id}")
                            break
                    else:
                        print(f"[SYNC] Flash server at {url} delete response status {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"[SYNC] Error notifying Flash server at {url} to delete proof {proof_id}: {e}")

        return {
            "pressure_notified": pressure_deleted,
            "flash_notified": flash_deleted
        }


sync_service = SyncService()