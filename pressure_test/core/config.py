import os
from pydantic import BaseModel

class Settings(BaseModel):
    CAMERA_SOURCE: str = "test_7.mp4"
    NO_FEED_IMAGE_PATH: str = "views/static/no_feed.jpg"
    MAIN_SERVER_HOST: str = "localhost"
    MAIN_SERVER_PORT: int = 8080
    CALIBRATION_RESULT_PATH: str = "calibration/calibration_result.npz"
    SYNC_API_TOKEN: str = "super_secure_sync_token_123"

settings = Settings()