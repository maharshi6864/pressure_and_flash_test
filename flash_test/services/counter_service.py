import time
import threading
from core.logger import get_logger

log = get_logger(__name__)


class CounterService:

    def __init__(self):
        self.holdtime = 5
        self.current_second = 0
        self.stop = False
        self.thread = None

    def count_down(self):
        self.current_second = 0

        while self.current_second < self.holdtime:
            if self.stop:
                self.current_second = 0
                log.info("Counter stopped.")
                return

            self.current_second += 1
            log.info(f"Second: {self.current_second}")
            time.sleep(1)

        log.info("Counter completed.")

    def start_counter(self):
        # Don't start another thread if one is already running
        if self.thread and self.thread.is_alive():
            log.info("Counter is already running.")
            return

        self.stop = False
        self.thread = threading.Thread(target=self.count_down, daemon=True)
        self.thread.start()

    def stop_counter(self):
        self.stop = True

counter_service = CounterService()