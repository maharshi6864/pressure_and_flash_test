from services.camera_service import camera_service
from core.logger import get_logger
from services.sync_server import sync_server

log = get_logger(__name__)

def startup_checks(engine):
  log.info("Intializing server startup checks.")
  camera_service.start()
  log.info("Startup checks complete.")
  sync_server.inform_main_server_alive()



    