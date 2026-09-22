import cv2
from datetime import datetime

# Open default camera
cap = cv2.VideoCapture("rtsp://admin:Admin@123@172.37.110.204:554/video/live?channel=1&subtype=0")

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Get camera resolution
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Fallback FPS if camera doesn't report it correctly
if fps <= 0 or fps > 120:
    fps = 30.0

# Timestamp filename
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = f"video_{timestamp}.mp4"

# Video writer
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

print(f"Recording: {filename}")
print("Press 'q' to stop recording.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Could not read frame.")
        break

    # Show live video
    cv2.imshow("Recording", frame)

    # Save frame
    out.write(frame)

    # Press q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"Video saved: {filename}")