import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S %p",
    handlers=[
        # Save logs to file
        # logging.FileHandler(LOG_FILE, encoding="utf-8"),

        # Also show logs in terminal
        logging.StreamHandler()
    ]
)


def get_logger(name):
    return logging.getLogger(name)