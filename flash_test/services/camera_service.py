import cv2
import threading
import time
from core.logger import get_logger
import numpy as np
from core.config import settings

log = get_logger(__name__)

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
        self._reference_captured = False

    def update_source(self, new_source: str):
        self.stop()
        self._reference_captured = False
        self.source = new_source
        self.start()

    def start(self):
        log.info("Starting Camera")
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
                    log.info("Camera disconnected.")
                    self.connected = False
                    time.sleep(2)
                    continue
                self.connected = True
                log.info("Camera connected.")
                self.status = "Connected"
                
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.cap.release()
                self.cap = None
                self.connected = False
                log.info("Camera disconnected.")
                self.status = "Disconnected"
                time.sleep(2)
                continue
                
            with self._frame_lock:
                self._recent_frame = frame.copy()
            
            if not self._reference_captured:
                self._reference_captured = True
                try:
                    from services.detect_flash_service import detect_flash_service
                    detect_flash_service.set_reference(frame)
                    # log.info(f"Reference image captured and saved to {settings.REFERENCE_IMAGE_PATH}")
                except Exception as e:
                    log.error(f"Failed to capture reference image: {e}")

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


def mjpeg_frame_generator(streaming_service: CameraService, processor=None):
    """
    HTTP MJPEG frame generator.
    `processor` is an optional function that takes a frame and returns a modified frame (e.g. drawn corners).
    """
    boundary = b"--frame"

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
            time.sleep(0.5) # Lower frequency for static placeholder
            continue

        frame = streaming_service.get_recent_frame()
        # frame = cv2.resize(frame,(1280,720))
        if frame is None:
            time.sleep(0.1)
            continue
            
        if processor:
            frame = processor(frame)

        # Encode frame as JPEG
        success, jpeg = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            continue

        yield (
                boundary + b"\r\n"
                           b"Content-Type: image/jpeg\r\n"
                           b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
                jpeg.tobytes() + b"\r\n"
        )

        time.sleep(1.0 / streaming_service.streaming_fps)

# Global camera service instance
camera_service = CameraService(settings.CAMERA_SOURCE)
