from repositories.current_objects import current_objects
import cv2
import numpy as np
import os
from core.config import settings

def estimate_pose_single_markers(corners, marker_size, camera_matrix, dist_coeffs):
    """
    Estimate pose for single markers with cross-version OpenCV compatibility.
    Uses cv2.aruco.estimatePoseSingleMarkers if available (older OpenCV on Raspberry Pi),
    otherwise falls back to cv2.solvePnP (OpenCV >= 4.7 / 5.x).
    """
    if hasattr(cv2.aruco, "estimatePoseSingleMarkers"):
        return cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, camera_matrix, dist_coeffs)

    marker_points = np.array([
        [-marker_size / 2,  marker_size / 2, 0],
        [ marker_size / 2,  marker_size / 2, 0],
        [ marker_size / 2, -marker_size / 2, 0],
        [-marker_size / 2, -marker_size / 2, 0]
    ], dtype=np.float32)

    corners = np.asarray(corners, dtype=np.float32)
    if corners.ndim == 2:
        corners = corners[np.newaxis, ...]

    rvecs, tvecs = [], []
    flag = getattr(cv2, "SOLVEPNP_IPPE_SQUARE", cv2.SOLVEPNP_ITERATIVE)
    for corner in corners:
        success, rvec, tvec = cv2.solvePnP(
            marker_points,
            corner,
            camera_matrix,
            dist_coeffs,
            flags=flag
        )
        if success:
            rvecs.append(rvec.reshape(1, 3))
            tvecs.append(tvec.reshape(1, 3))

    return np.array(rvecs), np.array(tvecs), None


class MeasurementService:
    def __init__(self):
        self.marker_id = 0
        self.marker_size = 0.05  # default 10 cm
        
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, cv2.aruco.DetectorParameters())
        
        self.camera_matrix = None
        self.dist_coeffs = None
        self.visible = False
        self.origin_x = None
        


        self.relative_x = 0.0
        
        self.max_positive_x = 0.0
        
        self.load_calibration()

    def load_calibration(self):
        if os.path.exists(settings.CALIBRATION_RESULT_PATH):
            calibration = np.load(settings.CALIBRATION_RESULT_PATH)
            self.camera_matrix = calibration["camera_matrix"]
            self.dist_coeffs = calibration["dist_coeffs"]
            return True
        return False

    def update_marker_size(self, size_m: float):
        self.marker_size = size_m

    def set_origin(self, current_x: float):
        print(current_x)
        self.origin_x = current_x
        self.relative_x = 0.0
        self.max_positive_x = 0.0

    def process_frame(self, frame):
        if frame is None:
            return frame
        og_frame = frame.copy()
        if self.camera_matrix is None:
            cv2.putText(frame, "Calibration data missing!", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame

        corners, ids, _ = self.detector.detectMarkers(frame)

        if ids is not None:
            ids = ids.flatten()
            for i, marker_id in enumerate(ids):
                if marker_id != self.marker_id:
                    
                    continue
                
                # y=400
                # x=500
                # w=640
                # h=480

                # frame = frame[y:y+h, x:x+w]
                cv2.aruco.drawDetectedMarkers(frame, [corners[i]])
                
                rvec, tvec, _ = estimate_pose_single_markers(
                    corners[i], self.marker_size, self.camera_matrix, self.dist_coeffs
                )

                cv2.drawFrameAxes(frame, self.camera_matrix, self.dist_coeffs, rvec[0], tvec[0], 0.05)
                current_x = tvec[0][0][0]
                if self.origin_x is None :
                    self.origin_x = current_x

                self.relative_x = current_x - self.origin_x
                if abs(self.relative_x) < 0.002:
                    self.relative_x = 0.0
                    
                # Update max positive and negative
                if self.relative_x > self.max_positive_x:
                    self.max_positive_x = self.relative_x
                    
                    if current_objects.lock == False:
                        current_objects.latest_maximum_x = self.relative_x
                        current_objects.latest_maximum_x_frame = og_frame.copy()
          
                pts = corners[i][0]
                center_x = int(np.mean(pts[:, 0]))
                center_y = int(np.mean(pts[:, 1]))
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

                # Store current_x so we can set origin
                self._last_current_x = current_x
        else:
            self.visible = False

        return frame

measurement_service = MeasurementService()
