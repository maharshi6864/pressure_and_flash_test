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
    # BIG ROI - WORKER DETECTION
    # ========================================================

    big_roi = frame[
        big_y1:big_y2,
        big_x1:big_x2
    ]

    big_gray = cv2.cvtColor(
        big_roi,
        cv2.COLOR_BGR2GRAY
    )

    big_gray = cv2.GaussianBlur(
        big_gray,
        (5, 5),
        0
    )

    big_diff = cv2.absdiff(
        big_gray,
        reference_big_gray
    )

    big_changed_mask = big_diff > 30

    big_changed_ratio = np.mean(
        big_changed_mask
    )

    person_present = (
        big_changed_ratio > 0.15
    )


    # ========================================================
    # FLASH CORE ROI
    # ========================================================
    #
    # THIS IS THE IMPORTANT PART.
    #
    # Based on your actual flash image:
    #
    # X = 680 -> 700
    # Y = 260 -> 330
    #
    # This is where the orange flash actually appears.
    #

    fx1 = 680
    fy1 = 260
    fx2 = 700
    fy2 = 330

    flash_roi = frame[
        fy1:fy2,
        fx1:fx2
    ]

    reference_roi = reference[
        fy1:fy2,
        fx1:fx2
    ]


    # ========================================================
    # CURRENT IMAGE - BGR
    # ========================================================

    b, g, r = cv2.split(
        flash_roi
    )

    b = b.astype(np.int16)
    g = g.astype(np.int16)
    r = r.astype(np.int16)


    # ========================================================
    # REFERENCE IMAGE - BGR
    # ========================================================

    rb, rg, rr = cv2.split(
        reference_roi
    )

    rb = rb.astype(np.int16)
    rg = rg.astype(np.int16)
    rr = rr.astype(np.int16)


    # ========================================================
    # 1. WARM / ORANGE DETECTION
    # ========================================================
    #
    # Flash:
    #
    # R > G
    # R > B
    #
    # White pants:
    #
    # R ~= G ~= B
    #
    # Therefore white pants fail this test.
    #

    warm_mask = (
        (r - g > 15) &
        (r - b > 35) &
        (r > 100)
    )


    # ========================================================
    # 2. REFERENCE WARM COLOR
    # ========================================================

    reference_warm = (
        (rr - rg > 15) &
        (rr - rb > 35) &
        (rr > 100)
    )


    # ========================================================
    # 3. IMPORTANT:
    #
    # We want NEW warm pixels.
    #
    # If the normal scene already contains an orange pixel
    # there, don't call it a flash.
    # ========================================================

    new_warm_mask = (
        warm_mask &
        ~reference_warm
    )


    # ========================================================
    # 4. BRIGHTNESS CHANGE
    # ========================================================

    current_gray = (
        0.114 * b +
        0.587 * g +
        0.299 * r
    )

    reference_gray = (
        0.114 * rb +
        0.587 * rg +
        0.299 * rr
    )


    brightness_difference = (
        current_gray -
        reference_gray
    )


    brightness_changed = (
        brightness_difference > 15
    )


    # ========================================================
    # 5. FINAL FLASH PIXELS
    # ========================================================
    #
    # Warm + NEW + brightness increase
    #

    flash_pixels = (
        new_warm_mask &
        brightness_changed
    )


    # ========================================================
    # 6. COUNT FLASH PIXELS
    # ========================================================

    flash_pixel_count = np.count_nonzero(
        flash_pixels
    )

    total_pixels = (
        flash_pixels.shape[0] *
        flash_pixels.shape[1]
    )

    flash_pixel_ratio = (
        flash_pixel_count /
        total_pixels
    )


    # ========================================================
    # 7. FIND WHERE THE FLASH IS
    # ========================================================

    flash_mask = (
        flash_pixels.astype(np.uint8) * 255
    )


    # IMPORTANT:
    #
    # DO NOT use 3x3 OPEN here.
    #
    # Your flash is too small.
    #

    # Just remove isolated single pixels.

    kernel = np.ones(
        (2, 2),
        np.uint8
    )

    flash_mask = cv2.morphologyEx(
        flash_mask,
        cv2.MORPH_CLOSE,
        kernel
    )


    # ========================================================
    # 8. CONNECTED COMPONENTS
    # ========================================================

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            flash_mask,
            connectivity=8
        )
    )


    best_component = None
    best_area = 0


    for i in range(1, num_labels):

        x, y, w, h, area = stats[i]

        if area <= 0:
            continue


        # Flash should be relatively vertical

        aspect_ratio = (
            h / max(w, 1)
        )


        # Don't require huge size.
        #
        # Your tiny flash can be very small.

        if (
            area >= 3 and
            h >= 5 and
            aspect_ratio >= 1.3 and
            w <= 15
        ):

            if area > best_area:

                best_area = area
                best_component = i


    # ========================================================
    # 9. FLASH DECISION
    # ========================================================
    #
    # Primary requirement:
    #
    # At least 5 warm pixels
    #
    # AND a vertical/localized component.
    #

    flash_detected = (
        flash_pixel_count >= 5 and
        best_component is not None
    )


    # ========================================================
    # 10. DRAW BIG ROI
    # ========================================================

    if person_present:
        big_color = (0, 0, 255)
    else:
        big_color = (0, 255, 0)

    cv2.rectangle(
        display,
        (big_x1, big_y1),
        (big_x2, big_y2),
        big_color,
        3
    )


    # ========================================================
    # 11. DRAW FLASH CORE ROI
    # ========================================================

    if flash_detected:
        flash_color = (0, 0, 255)
    else:
        flash_color = (0, 255, 0)

    cv2.rectangle(
        display,
        (fx1, fy1),
        (fx2, fy2),
        flash_color,
        2
    )


    # ========================================================
    # 12. DRAW DETECTED FLASH
    # ========================================================

    if best_component is not None:

        x, y, w, h, area = stats[
            best_component
        ]

        cv2.rectangle(
            display,

            (
                fx1 + x,
                fy1 + y
            ),

            (
                fx1 + x + w,
                fy1 + y + h
            ),

            (255, 0, 255),

            2
        )


    # ========================================================
    # 13. DEBUG VALUES
    # ========================================================

    warm_ratio = (
        np.mean(warm_mask)
    )

    new_warm_ratio = (
        np.mean(new_warm_mask)
    )

    brightness_ratio = (
        np.mean(brightness_changed)
    )


    # ========================================================
    # 14. STATUS
    # ========================================================

    if flash_detected:

        status = "FLASH DETECTED"
        status_color = (0, 0, 255)

    elif person_present:

        status = "WORKER PRESENT - NO FLASH"
        status_color = (0, 165, 255)

    else:

        status = "NO FLASH"
        status_color = (0, 255, 0)


    # ========================================================
    # 15. DISPLAY
    # ========================================================

    cv2.putText(
        display,
        status,
        (30, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        status_color,
        3
    )

    cv2.putText(
        display,
        f"Flash Pixels: {flash_pixel_count}",
        (30, 105),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Flash Ratio: {flash_pixel_ratio:.4f}",
        (30, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Warm Ratio: {warm_ratio:.4f}",
        (30, 175),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"New Warm: {new_warm_ratio:.4f}",
        (30, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Brightness Change: {brightness_ratio:.4f}",
        (30, 245),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Big ROI: {big_changed_ratio:.4f}",
        (30, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )

    cv2.putText(
        display,
        f"Worker: {'YES' if person_present else 'NO'}",
        (30, 315),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        status_color,
        2
    )


    return flash_detected, display, frame


# ============================================================
# VIDEO
# ============================================================

cap = cv2.VideoCapture(
    "aa_recordings/test_3.mp4"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break

    # frame = cv2.imread('/Users/maharshipatel/Desktop/shutt_p/raw_scripts/1_2.jpg')

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