import datetime
import time
import cv2
import numpy as np
import time 
# Load a normal frame (NO FLASH)
reference = cv2.imread(r"1.jpg")
output_path = r"flash_detected_images"

# Adjust this ROI to cover only the expected flash area
x1, y1, x2, y2 = 685, 265, 695, 370

reference_roi = reference[y1:y2, x1:x2]
reference_gray = cv2.cvtColor(reference_roi, cv2.COLOR_BGR2GRAY)


def detect_flash(frame):
    roi = frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # 1. Detect extremely bright pixels
    bright_mask = gray > 245
    bright_ratio = np.mean(bright_mask)

    # 2. Compare against normal background
    diff = cv2.absdiff(gray, reference_gray)
    changed_ratio = np.mean(diff > 80)

    # Flash should cause both strong brightness
    # and a large difference from normal background
    flash_detected = (
        bright_ratio > 0.05 and
        changed_ratio > 0.10
    )

    # Visualization
    display = frame.copy()

    color = (0, 0, 255) if flash_detected else (0, 255, 0)

    cv2.rectangle(display, (x1, y1), (x2, y2), color, 3)
  
    status = f"FLASH DETECTED {bright_ratio}" if flash_detected else f"NO FLASH {bright_ratio}"

    cv2.putText(
        display,
        status,
        (30, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        color,
        3
    )

    cv2.putText(
        display,
        f'Brightness Ration : {str(bright_ratio)}',
        (30, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        color,
        3
    )

    cv2.putText(
        display,
        f'Changed Ration : {str(changed_ratio)}',
        (30, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        color,
        3
    )

    # print(f"Chnaged Ratio : {str(changed_ratio)}")
    # print(f"Brightness Ratio : {str(bright_ratio)}")


    return flash_detected, display , frame


cap = cv2.VideoCapture("aa_recordings/test_6.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    detected, display, frame = detect_flash(frame)
    if detected:
      cv2.imwrite(f"{output_path}/flash{datetime.datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}.jpeg",frame)
    cv2.imshow("Flash Detection", display)
    # time.sleep(1)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    # time.sleep(0.)

cap.release()
cv2.destroyAllWindows()