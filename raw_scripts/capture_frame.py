import cv2



cap = cv2.VideoCapture("/Users/maharshipatel/Desktop/shutt_p/raw_scripts/test_videos    /test_6.mp4")


while True:


    ret, frame = cap.read()
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite("6.jpg",frame)
        break
    

