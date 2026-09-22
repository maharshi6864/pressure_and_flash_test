import datetime
import cv2
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

# Normal frame WITHOUT worker / flash
reference = cv2.imread(r"1.jpg")

output_path = r"flash_detected_images"


# ------------------------------------------------------------
# SMALL ROI - Flash detection
# ------------------------------------------------------------
# flash_x1, flash_y1, flash_x2, flash_y2 = 685, 267, 697, 270
flash_x1, flash_y1, flash_x2, flash_y2 = 670, 250, 710, 400

# ------------------------------------------------------------
# BIG ROI - Worker / scene-change detection
#
# x = 465
# y = 180
# w = 450
# h = 480
# ------------------------------------------------------------
big_x = 465
big_y = 180
big_w = 450
big_h = 480

big_x1 = big_x
big_y1 = big_y
big_x2 = big_x + big_w
big_y2 = big_y + big_h


# ============================================================
# PREPARE REFERENCE IMAGE
# ============================================================

# ----- Small flash ROI reference -----

reference_flash_roi = reference[
    flash_y1:flash_y2,
    flash_x1:flash_x2
]

reference_flash_gray = cv2.cvtColor(
    reference_flash_roi,
    cv2.COLOR_BGR2GRAY
)


# ----- Big ROI reference -----

reference_big_roi = reference[
    big_y1:big_y2,
    big_x1:big_x2
]

reference_big_gray = cv2.cvtColor(
    reference_big_roi,
    cv2.COLOR_BGR2GRAY
)

# Blur reference to reduce camera noise/compression noise
reference_big_gray = cv2.GaussianBlur(
    reference_big_gray,
    (5, 5),
    0
)


# ============================================================
# DETECTION
# ============================================================

def detect_flash(frame):

    display = frame.copy()


    # ========================================================
    # 1. BIG ROI - Detect worker / scene change
    # ========================================================

    big_roi = frame[
        big_y1:big_y2,
        big_x1:big_x2
    ]

    big_gray = cv2.cvtColor(
        big_roi,
        cv2.COLOR_BGR2GRAY
    )

    # Reduce small camera/compression noise
    big_gray = cv2.GaussianBlur(
        big_gray,
        (5, 5),
        0
    )

    # Compare current BIG ROI against permanent reference
    big_diff = cv2.absdiff(
        big_gray,
        reference_big_gray
    )

    # Pixels that changed significantly
    big_changed_mask = big_diff > 30

    # Percentage of BIG ROI that changed
    big_changed_ratio = np.mean(
        big_changed_mask
    )


    # ========================================================
    # 2. Determine whether worker is present
    # ========================================================

    # Tune this value.
    #
    # Example:
    # 0.05 = 5% of big ROI changed
    # 0.10 = 10%
    # 0.20 = 20%
    #
    BIG_ROI_CHANGE_THRESHOLD = 0.15

    person_present = (
        big_changed_ratio > BIG_ROI_CHANGE_THRESHOLD
    )


    # ========================================================
    # 3. SMALL ROI - Flash detection
    # ========================================================

    flash_roi = frame[
        flash_y1:flash_y2,
        flash_x1:flash_x2
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
        reference_flash_gray
    )

    changed_ratio = np.mean(
        flash_diff > 80
    )


    # ========================================================
    # 4. FLASH DECISION
    # ========================================================

    # Existing flash conditions
    flash_conditions = (
        bright_ratio > 0.05 and
        changed_ratio > 0.10
    )


    # IMPORTANT:
    #
    # If the BIG ROI has changed, we assume that the worker
    # is standing/moving in front of the camera.
    #
    # Therefore DO NOT allow the small ROI to report a flash.
    #
    flash_detected = (
        not person_present and
        flash_conditions
    )


    # ========================================================
    # 5. DRAW BIG ROI
    # ========================================================

    if person_present:
        big_color = (0, 0, 255)       # RED
    else:
        big_color = (0, 255, 0)       # GREEN

    cv2.rectangle(
        display,
        (big_x1, big_y1),
        (big_x2, big_y2),
        big_color,
        3
    )


    # ========================================================
    # 6. DRAW SMALL FLASH ROI
    # ========================================================

    if flash_detected:
        flash_color = (0, 0, 255)     # RED
    else:
        flash_color = (0, 255, 0)     # GREEN

    cv2.rectangle(
        display,
        (flash_x1, flash_y1),
        (flash_x2, flash_y2),
        flash_color,
        1
    )


    # ========================================================
    # 7. DISPLAY STATUS
    # ========================================================

    if flash_detected:

        status = f"FLASH DETECTED {bright_ratio:.4f}"
        status_color = (0, 0, 255)

    elif person_present:

        status = f"WORKER PRESENT - FLASH IGNORED"
        status_color = (0, 165, 255)

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

    cv2.putText(
        display,
        f"Big ROI Changed Ratio: {big_changed_ratio:.4f}",
        (30, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Worker: {'YES' if person_present else 'NO'}",
        (30, 215),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )


    return flash_detected, display, frame


# ============================================================
# VIDEO
# ============================================================

# cap = cv2.VideoCapture(
#     "aa_recordings/test_6.mp4"
# )


while True:

    # ret, frame = cap.read()

    # if not ret:
    #     break

    frame = cv2.imread('/Users/maharshipatel/Desktop/shutt_p/raw_scripts/1_2.jpg')

    detected, display, frame = detect_flash(frame)


    # ========================================================
    # SAVE FLASH IMAGE
    # ========================================================

    if detected:

        filename = (
            f"{output_path}/flash"
            f"{datetime.datetime.now().strftime('%d-%m-%Y_%I-%M-%S_%p')}"
            f".jpeg"
        )

        cv2.imwrite(
            filename,
            display
        )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        "Flash Detection",
        display
    )


    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()