


def check_obstacle_in_between():
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

    return False