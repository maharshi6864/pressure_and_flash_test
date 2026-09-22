import os
from pydantic import BaseModel


class Settings(BaseModel):
    CAMERA_SOURCE: str = r"test_videos/test_8.mp4"
    NO_FEED_IMAGE_PATH: str = "views/static/no_feed.jpg"
    REFERENCE_IMAGE_PATH: str = "reference_image.jpg"
    FLASH_IMAGES_DIR: str = "saved_images/flash_tests"
    MAIN_SERVER_HOST: str = "localhost"
    MAIN_SERVER_PORT: int = 8080
    MAIN_SERVER_URL: str = "http://localhost:8080"
    SYNC_API_TOKEN: str = "super_secure_sync_token_123"


settings = Settings()
