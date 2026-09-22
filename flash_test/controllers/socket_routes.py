from repositories.current_objects import CurrentObjects
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from services.camera_service import camera_service

router = APIRouter()

@router.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    try:
        last_status = None
        while True:
            current_status = camera_service.status
            if current_status != last_status:
                await websocket.send_json({"status": current_status})
                last_status = current_status
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass

@router.websocket("/ws/test_info")
async def websocket_test_info(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "current_test_id": CurrentObjects.current_test_id,
                "flash_detected":CurrentObjects.flash_detection
            })
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        pass
