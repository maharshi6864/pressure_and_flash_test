import cv2
import os

# Create folder if it doesn't exist
SAVE_DIR = "calibration_images"
os.makedirs(SAVE_DIR, exist_ok=True)

# RTSP_URL = "rtsp://admin:Mipl@123@192.168.1.188:554/stream0"
RTSP_URL = 1

# Open camera
cap = cv2.VideoCapture(RTSP_URL)

count = 0

print("Press SPACE to capture an image.")
print("Press ESC to finish.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    cv2.putText(
        frame,
        f"Images: {count}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0,255,0),
        2
    )
    frame = cv2.resize(frame,(1280,720))
    cv2.imshow("Calibration Capture", frame)

    key = cv2.waitKey(1)

    if key == 32:   # SPACE

        filename = os.path.join(SAVE_DIR, f"{count:02d}.jpg")

        cv2.imwrite(filename, frame)

        print("Saved:", filename)

        count += 1

    elif key == 27:   # ESC
        break

cap.release()
cv2.destroyAllWindows()