import os
import cv2

video_path = 'aa_recordings/test_1.mp4'
save_path = 'flash_frames'

os.makedirs(save_path, exist_ok=True)

cap = cv2.VideoCapture(video_path)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Current frame index
current_frame = 0

while True:

    # Jump to the required frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    ret, frame = cap.read()

    if not ret:
        print("Could not read frame.")
        break

    # Show frame information
    display_frame = frame.copy()

    cv2.putText(
        display_frame,
        f"Frame: {current_frame + 1}/{total_frames}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Display", display_frame)

    print(
        f"Frame {current_frame + 1} | "
        "S = Save | D = Next | A = Previous | Q = Quit"
    )

    key = cv2.waitKey(0) & 0xFF

    # S = Save current frame
    if key == ord('s'):

        # Use original video frame number as filename
        file_path = os.path.join(
            save_path,
            f"frame_{current_frame + 1}.jpg"
        )

        cv2.imwrite(file_path, frame)

        print(f"Saved: {file_path}")

        # Automatically move to next frame
        current_frame += 1

    # D = Skip / Next frame
    elif key == ord('d'):

        current_frame += 1

    # A = Go to previous frame
    elif key == ord('a'):

        current_frame -= 1

        # Prevent going before first frame
        if current_frame < 0:
            current_frame = 0

    # Q = Quit
    elif key == ord('q'):

        break

    # Prevent going beyond last frame
    if current_frame >= total_frames:
        print("Reached the end of the video.")
        break


cap.release()
cv2.destroyAllWindows()