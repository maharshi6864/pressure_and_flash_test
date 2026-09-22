from datetime import datetime
import cv2
import threading
import numpy as np
import logging
import asyncio
import time

from socket_controller.camera_status_socket_controller import camera_status_manager

logging.basicConfig(level=logging.INFO)


class StreamingService:
    def __init__(
        self,
        camera_id: int,
        position: str,
        rtsp_url: str,
        streaming_fps: int = 15,
        feed_rotation: int = 0,
            loop=None,
    ):
        self._watchdog_thread = None
        self.streaming_status= True
        self._frame_lock = threading.Lock()
        self.id = camera_id
        self.position = position
        self.rtsp_url = rtsp_url
        self.streaming_fps = streaming_fps
        self.running = False
        self.recent_frame = None
        self.online_status = "Offline"
        self.retry_delay = 2
        self.cap = None
        self.feed_rotation = feed_rotation
        self.thread = None
        self.connected = False
        self._stop_event = threading.Event()
        self.loop = loop or asyncio.get_event_loop()
        self._last_frame_ts = 0
        self.frame_timeout = 3.0  # seconds (your requirement)
        self._disconnect_requested = False
        print("CAMERA Poisition : ",self.position)
        print("Camera Rotation Required : ",self.feed_rotation)

    # --------------------------------------------
    def start(self):
        if self.running:
            return

        self.running = True
        self._last_frame_ts = time.time()
        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self.thread.start()

        self._watchdog_thread = threading.Thread(
            target=self._watchdog,
            daemon=True
        )
        self._watchdog_thread.start()

    def _notify(self, status: str):
        self.online_status = status
        asyncio.run_coroutine_threadsafe(
            camera_status_manager.send_json({
                "camera_id": self.id,
                "status": status
            }),
            self.loop
        )

    def get_recent_frame(self):
        with self._frame_lock:
            if self._recent_frame is None:
                return None
            return self._recent_frame.copy()

    def _connect_camera(self):
        self._notify("Reconnecting...")

        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Hard open check
        if not cap.isOpened():
            cap.release()
            return None

        return cap

    def _watchdog(self):
        while self.running:
            if self.connected:
                if time.time() - self._last_frame_ts > self.frame_timeout:
                    logging.warning(
                        f"Camera {self.id}: watchdog timeout"
                    )
                    self._notify("Reconnecting...")
                    self._disconnect_requested = True
            time.sleep(0.5)

    def _force_disconnect(self):
        # DO NOT touch cap here
        self.connected = False
        self._disconnect_requested = True
        self._notify("Offline")

    def _run(self):
        self.cap = None

        while self.running:

            # -------- CONNECT --------
            if self.cap is None:
                cap = self._connect_camera()
                if cap is None:
                    self._notify("Offline")
                    time.sleep(self.retry_delay)
                    continue

                self.cap = cap
                self.connected = True
                self._disconnect_requested = False

                self._notify("Online")
                logging.info("Camera connected")

            # -------- READ FRAME --------
            try:
                ret, frame = self.cap.read()
                if self.feed_rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            except cv2.error as e:
                logging.error(f"OpenCV read crash: {e}")
                ret = False

            # -------- DISCONNECT --------
            if not ret or frame is None or self._disconnect_requested or not self.running:
                logging.warning("Dropping camera connection safely")

                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception as e:
                        logging.error(f"Release failed: {e}")
                    finally:
                        self.cap = None

                self.connected = False
                self._disconnect_requested = False

                if self.running:
                    self._notify("Offline")
                    time.sleep(self.retry_delay)
                continue
                
            # -------- SUCCESS --------
            self._last_frame_ts = time.time()
            with self._frame_lock:
                self._recent_frame = frame.copy()

    def stop(self):
        self.running = False
        self._disconnect_requested = True

        if self.thread:
            self.thread.join(timeout=2)
        self._notify("Offline")
