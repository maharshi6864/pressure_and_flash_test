from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from services.camera_service import camera_service
from services.measurement_service import measurement_service
from core.lookup_table import inch_lookup
from repositories.current_objects import current_objects

router = APIRouter()

def get_lookup_data(distance_m):
    if distance_m is None:
        return {"inch": "0 inch", "psi": 0.0, "mpa": 0.0}
    distance_mm = abs(distance_m * 1000)
    if distance_mm < 1.0: # Very small distance, just return 0s
        return {"inch": "0 inch", "psi": 0.0, "mpa": 0.0}
    inches = distance_mm / 25.4
    total_32nds = round(inches * 32)
    if total_32nds >= 51:
        total_32nds -= 2
    
    data = inch_lookup.get(str(total_32nds))
    if data:
        return data
    else:
        # Construct fraction if not in table
        whole = total_32nds // 32
        frac = total_32nds % 32
        if whole > 0 and frac > 0:
            inch_str = f"{whole}-{frac}/32 inch"
        elif whole > 0:
            inch_str = f"{whole} inch"
        else:
            inch_str = f"{frac}/32 inch"
        return {"inch": inch_str, "psi": 0.0, "mpa": 0.0}

@router.websocket("/ws/measurements")
async def websocket_measurements(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            current_lookup = get_lookup_data(measurement_service.relative_x)
            max_pos_lookup = get_lookup_data(measurement_service.max_positive_x)
            rec_pos_lookup = get_lookup_data(current_objects.latest_maximum_x)
            data = {
                "relative_x": measurement_service.relative_x,
                "current_lookup": current_lookup,
                "max_positive_x": measurement_service.max_positive_x,
                "max_pos_lookup": max_pos_lookup,
                "rec_pos_lookup": rec_pos_lookup,
                "rec_positive_x": current_objects.latest_maximum_x,
            }
            await websocket.send_json(data)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
