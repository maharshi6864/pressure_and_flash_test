import cv2
import numpy as np

# ======================================
# Load Camera Calibration
# ======================================
calibration = np.load("calibration_result.npz")

camera_matrix = calibration["camera_matrix"]
dist_coeffs = calibration["dist_coeffs"]

# ======================================
# ArUco Settings
# ======================================
MARKER_ID = 0
MARKER_SIZE = 0.10  # 10 cm

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

detector = cv2.aruco.ArucoDetector(
    aruco_dict,
    cv2.aruco.DetectorParameters()
)


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


# ======================================
# Camera
# ======================================
RTSP_URL = "rtsp://admin:Mipl@123@192.168.1.188:554/stream1"

cap = cv2.VideoCapture(RTSP_URL)

if not cap.isOpened():
    raise RuntimeError("Cannot open camera.")

# ======================================
# Variables
# ======================================
origin_x = None
relative_x = 0.0

print("Press SPACE to set current X position as ZERO.")
print("Press ESC to exit.")

# ======================================
# Main Loop
# ======================================
while True:

    ret, frame = cap.read()

    if not ret:
        break

    corners, ids, _ = detector.detectMarkers(frame)

    if ids is not None:

        ids = ids.flatten()

        for i, marker_id in enumerate(ids):

            if marker_id != MARKER_ID:
                continue

            # Draw marker
            cv2.aruco.drawDetectedMarkers(frame, [corners[i]])

            # Pose estimation
            rvec, tvec, _ = estimate_pose_single_markers(
                corners[i],
                MARKER_SIZE,
                camera_matrix,
                dist_coeffs
            )

            # Draw coordinate axes
            cv2.drawFrameAxes(
                frame,
                camera_matrix,
                dist_coeffs,
                rvec[0],
                tvec[0],
                0.05
            )

            # Current X position (meters)
            current_x = tvec[0][0][0]

            # Calculate relative X
            if origin_x is not None:
                relative_x = current_x - origin_x

                # Ignore tiny noise (2 mm)
                if abs(relative_x) < 0.002:
                    relative_x = 0.0

            # Print continuously
            print(
                f"\rRelative X : {relative_x:+.4f} m ({relative_x*100:.2f} cm)",
                end=""
            )

            # Marker center
            pts = corners[i][0]

            center_x = int(np.mean(pts[:, 0]))
            center_y = int(np.mean(pts[:, 1]))

            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

            cv2.putText(
                frame,
                f"Relative X : {relative_x:+.3f} m",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"{relative_x*100:+.1f} cm",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

    frame = cv2.resize(frame, (1280, 720))
    cv2.imshow("ArUco Tracker", frame)

    key = cv2.waitKey(1) & 0xFF

    # Set current position as origin
    if key == ord(' '):

        if ids is not None:
            origin_x = current_x
            relative_x = 0.0

            print("\n")
            print("=" * 40)
            print(f"Origin Set : {origin_x:.4f} m")
            print("=" * 40)

    elif key == 27:
        break

cap.release()
cv2.destroyAllWindows()