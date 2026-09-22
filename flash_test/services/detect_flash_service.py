from services.counter_service import counter_service
import cv2
from core.database import SessionLocal
import numpy as np
import os
from core.config import settings
from repositories.current_objects import CurrentObjects 
from datetime import datetime
from services.test_service import test_service

class DetectFlashService:
    def __init__(self):
        self.flash_x1 = 685
        self.flash_y1 = 265
        self.flash_x2 = 695
        self.flash_y2 = 370

        self.big_x1 = 465
        self.big_y1 = 180
        self.big_x2 = 915
        self.big_y2 = 660
        self.reference_flash_roi = None
        self.reference_flash_gray = None
        self.reference_big_roi = None
        self.reference_big_gray = None
        self.reference = None

    def set_reference(self, frame):
        if frame is not None:
            self.reference = frame.copy()

            self.reference_flash_roi = self.reference[
                self.flash_y1:self.flash_y2,
                self.flash_x1:self.flash_x2
            ]

            self.reference_flash_gray = cv2.cvtColor(
                self.reference_flash_roi,
                cv2.COLOR_BGR2GRAY
            )

            # ----- Big ROI reference -----

            self.reference_big_roi = self.reference[
                self.big_y1:self.big_y2,
                self.big_x1:self.big_x2
            ]

            self.reference_big_gray = cv2.cvtColor(
                self.reference_big_roi,
                cv2.COLOR_BGR2GRAY
            )

            # Blur reference to reduce camera noise/compression noise
            self.reference_big_gray = cv2.GaussianBlur(
                self.reference_big_gray,
                (5, 5),
                0
            )

    def __detect_flash__(self, frame):
        if self.reference is None:
            self.set_reference(frame)
            return False, frame.copy()

        display = frame.copy()

        
        flash_roi = frame[
            self.flash_y1:self.flash_y2,
            self.flash_x1:self.flash_x2
        ]

        flash_gray = cv2.cvtColor(
            flash_roi,
            cv2.COLOR_BGR2GRAY
        )

        # --------------------------------------------------------
        # Brightness detection
        # --------------------------------------------------------

        bright_mask = flash_gray > 245

        bright_ratio = np.mean(
            bright_mask
        )

        # --------------------------------------------------------
        # Difference from normal reference
        # --------------------------------------------------------

        flash_diff = cv2.absdiff(
            flash_gray,
            self.reference_flash_gray
        )

        changed_ratio = np.mean(
            flash_diff > 80
        )

        # ========================================================
        # 4. FLASH DECISION
        # ========================================================

        # Existing flash conditions
        flash_detected = (
                # bright_ratio > 0.05 and
                changed_ratio > 0.10
        )


        # ========================================================
        # 5. DRAW SMALL FLASH ROI
        # ========================================================

        if flash_detected:
            flash_color = (0, 0, 255)  # RED
        else:
            flash_color = (0, 255, 0)  # GREEN

        cv2.rectangle(
            display,
            (self.flash_x1, self.flash_y1),
            (self.flash_x2, self.flash_y2),
            flash_color,
            3
        )

        # ========================================================
        # 7. DISPLAY STATUS
        # ========================================================

        if flash_detected:

            status = f"FLASH DETECTED {bright_ratio:.4f}"
            status_color = (0, 0, 255)
        else:

            status = f"NO FLASH {bright_ratio:.4f}"
            status_color = (0, 255, 0)

        cv2.putText(
            display,
            status,
            (30, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            status_color,
            3
        )

        # ========================================================
        # 8. DEBUG INFORMATION
        # ========================================================

        cv2.putText(
            display,
            f"Flash Brightness Ratio: {bright_ratio:.4f}",
            (30, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            status_color,
            2
        )

        cv2.putText(
            display,
            f"Flash Changed Ratio: {changed_ratio:.4f}",
            (30, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            status_color,
            2
        )

      
        return flash_detected, display

    def process_frame(self, frame):
        if frame is None:
            return frame
        flash_detected, display_frame = self.__detect_flash__(frame)
        
        # Store most recent frames for manual save or end test
        CurrentObjects.latest_frame = frame
        CurrentObjects.latest_display_frame = display_frame

        if not CurrentObjects.ready_status:
            return display_frame

        if flash_detected and CurrentObjects.current_test_id is not None:
            CurrentObjects.flash_detection_image = display_frame
            CurrentObjects.flash_image = display_frame
            CurrentObjects.flash_detection = True
            CurrentObjects.flash_detected_time = datetime.now()

        return display_frame


detect_flash_service = DetectFlashService()
