import cv2
import numpy as np
import glob

# Chessboard settings
CHESSBOARD_SIZE = (9, 6)
SQUARE_SIZE = 0.025  # 25 mm = 0.025 meters

# Prepare object points
objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[
    0:CHESSBOARD_SIZE[0],
    0:CHESSBOARD_SIZE[1]
].T.reshape(-1, 2)

objp *= SQUARE_SIZE

objpoints = []
imgpoints = []

images = glob.glob("calibration_images/*.jpg")

if len(images) == 0:
    raise Exception("No calibration images found.")

print(f"Found {len(images)} images")

for fname in images:

    image = cv2.imread(fname)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    found, corners = cv2.findChessboardCorners(
        gray,
        CHESSBOARD_SIZE,
        None
    )

    if found:

        corners = cv2.cornerSubPix(
            gray,
            corners,
            (11,11),
            (-1,-1),
            (
                cv2.TERM_CRITERIA_EPS +
                cv2.TERM_CRITERIA_MAX_ITER,
                30,
                0.001
            )
        )

        objpoints.append(objp)
        imgpoints.append(corners)

        cv2.drawChessboardCorners(
            image,
            CHESSBOARD_SIZE,
            corners,
            found
        )

        cv2.imshow("Corners", image)
        cv2.waitKey(300)

cv2.destroyAllWindows()

ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
    objpoints,
    imgpoints,
    gray.shape[::-1],
    None,
    None
)

print("\nCalibration Finished\n")

print("Camera Matrix\n")
print(camera_matrix)

print("\nDistortion Coefficients\n")
print(dist_coeffs)

np.savez(
    "calibration_result.npz",
    camera_matrix=camera_matrix,
    dist_coeffs=dist_coeffs
)

print("\nSaved calibration_result.npz")

# Calculate reprojection error
total_error = 0

for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(
        objpoints[i],
        rvecs[i],
        tvecs[i],
        camera_matrix,
        dist_coeffs
    )

    error = cv2.norm(
        imgpoints[i].reshape(-1, 1, 2),
        imgpoints2.reshape(-1, 1, 2),
        cv2.NORM_L2
    ) / len(imgpoints2)

    total_error += error

print(f"\nAverage Reprojection Error: {total_error / len(objpoints):.5f}")