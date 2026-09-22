from services.camera_service import camera_service
from services.sync_server import sync_server


async def startup_checks(engine):
    camera_service.start()
    sync_server.inform_main_server_alive()