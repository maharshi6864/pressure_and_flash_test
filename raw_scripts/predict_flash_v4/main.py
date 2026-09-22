import datetime
import cv2
import numpy as np

reference = cv2.imread(r"1.jpg")

output_path = r"flash_detected_images"


# ------------------------------------------------------------
# SMALL ROI - Flash detection
# ------------------------------------------------------------
# flash_x1, flash_y1, flash_x2, flash_y2 = 685, 267, 697, 270
flash_x1, flash_y1, flash_x2, flash_y2 = 670, 250, 710, 400




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