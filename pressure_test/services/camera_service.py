import cv2
import threading
import time
import logging
import numpy as np
import asyncio
from core.config import settings

logging.basicConfig(level=logging.INFO)

class CameraService:
    def __init__(self, source: str, streaming_fps: int = 30):
        self.source = source
        self.streaming_fps = streaming_fps
        self.running = False
        self.connected = False
        self._recent_frame = None
        self._frame_lock = threading.Lock()
        self.cap = None
        self.thread = None
        self.status = "Disconnected"

    def update_source(self, new_source: str):
        self.stop()
        self.source = new_source
        self.start()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def get_recent_frame(self):
        with self._frame_lock:
            if self._recent_frame is None:
                return None
            return self._recent_frame.copy()

    def _connect(self):
        self.status = "Reconnecting..."
        
        # Handle USB vs RTSP
        source = int(self.source) if self.source.isdigit() else self.source
        
        cap = cv2.VideoCapture(source)
        if type(source) == str and cap.isOpened():
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            cap.release()
            return None
        return cap

    def _run(self):
        while self.running:
            if self.cap is None:
                self.cap = self._connect()
                if self.cap is None:
                    self.status = "Disconnected"
                    self.connected = False
                    time.sleep(2)
                    continue
                self.connected = True
                self.status = "Connected"
                
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                self.cap = None
                self.connected = False
                self.status = "Disconnected"
                time.sleep(2)
                continue
            # y=400
            # x=500
            # w=640
            # h=480
            # frame = frame[y:y+h, x:x+w]
            with self._frame_lock:
                self._recent_frame = frame.copy()
            
            time.sleep(1.0 / self.streaming_fps)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.connected = False
        self.status = "Disconnected"


async def mjpeg_frame_generator(streaming_service: CameraService, processor=None):
    """
    HTTP MJPEG frame generator.
    `processor` is an optional function that takes a frame and returns a modified frame (e.g. drawn corners).
    """
    boundary = b"--frame"

    try:
        while True:
            if streaming_service is None or not streaming_service.running or not streaming_service.connected:
                # Load placeholder image
                # placeholder_path = settings.NO_FEED_IMAGE_PATH
                # frame = cv2.imread(placeholder_path)
                # if frame is None:
                    # Fallback to black frame if placeholder missing
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "No Feed", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                
                success, jpeg = cv2.imencode(".jpg", frame)
                if success:
                    yield (
                            boundary + b"\r\n"
                                       b"Content-Type: image/jpeg\r\n"
                                       b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                            jpeg.tobytes() + b"\r\n"
                    )
                await asyncio.sleep(0.5) # Lower frequency for static placeholder
                continue

            frame = streaming_service.get_recent_frame()
            # frame = cv2.resize(frame,(1280,720))
            if frame is None:
                await asyncio.sleep(0.1)
                continue
                
            if processor:
                frame = processor(frame)

            success, jpeg = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY, 80]
            )

            if not success:
                await asyncio.sleep(0.1)
                continue

            yield (
                    boundary + b"\r\n"
                               b"Content-Type: image/jpeg\r\n"
                               b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                    jpeg.tobytes() + b"\r\n"
            )

            await asyncio.sleep(1.0 / streaming_service.streaming_fps)
    except asyncio.CancelledError:
        pass

# Global camera service instance
camera_service = CameraService(settings.CAMERA_SOURCE)
