import cv2
import json
import os
import time

JSON_PATH = "crop.json"


def load_crop():
    try:
        with open(JSON_PATH, "r") as f:
            data = json.load(f)

        return (
            data["x"],
            data["y"],
            data["w"],
            data["h"]
        )

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Could not load crop settings: {e}")
        return None


# Initial crop
crop = load_crop()

# Track when JSON was last modified
last_modified = os.path.getmtime(JSON_PATH)

# cap = cv2.VideoCapture(1)


while True:
    # Check if JSON changed
    try:
        current_modified = os.path.getmtime(JSON_PATH)

        if current_modified != last_modified:
            new_crop = load_crop()

            if new_crop is not None:
                crop = new_crop
                print("Crop updated:", crop)

            last_modified = current_modified

    except FileNotFoundError:
        pass

    # ret, frame = cap.read()
    frame = cv2.imread("/Users/maharshipatel/Desktop/shutt_p/raw_scripts/1_2.jpg")
    # frame_2 = cv2.imread("/Users/maharshipatel/Desktop/shutt_p/flash_test/raw_scripts/test_1_frame.jpeg")
    
    # height, width, channels = frame.shape
    # print(height,width)
    # if not ret:
    #     cap = cv2.VideoCapture('pressure_test_sample_video.mp4')
    if crop is not None:
        x, y, w, h = crop

        # cropped_frame = frame[y:y+h, x:x+w]
        cv2.rectangle(frame, (x, y), (x + w , y + h), (0, 255, 0), 1)
        # cv2.rectangle(frame_2, (x, y), (x + w , y + h), (0, 255, 0), 2)


    cv2.imshow("Frame", frame)
    # cv2.imshow("Frame 2", frame_2)
    # cv2.imshow("Cropped Frame", cropped_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite("cropped_frame.jpg",frame)
        break

cap.release()
cv2.destroyAllWindows()