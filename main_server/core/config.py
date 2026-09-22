import os

class Settings:
    pressure_test_server_url = os.getenv("PRESSURE_TEST_SERVER_URL", "http://127.0.0.1:8081")
    flash_test_server_url = os.getenv("FLASH_TEST_SERVER_URL", "http://127.0.0.1:8082")
    SYNC_API_TOKEN = os.getenv("SYNC_API_TOKEN", "super_secure_sync_token_123")

