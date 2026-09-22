import cv2
import os
from datetime import datetime
import numpy as np  

RTSP_URL = "rtsp://admin:Mipl@123@192.168.1.188:554/stream0"

cap = cv2.VideoCapture(RTSP_URL,)

if not cap.isOpened():
    print("❌ Error: Unable to open RTSP stream")
    exit(1)


while True:
    ret, frame = cap.read()
    frame = cv2.resize(frame,(1280,720))
    
    cv2.imshow("TESTING CAMERA", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
