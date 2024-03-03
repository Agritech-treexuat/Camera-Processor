import cv2

from yolov8 import YOLOv8
from datetime import datetime


# Initialize the webcam
cap = cv2.VideoCapture(0)

# Initialize YOLOv7 object detector
model_path = "models/yolov8m.onnx"
yolov8_detector = YOLOv8(model_path, conf_thres=0.5, iou_thres=0.5)

cv2.namedWindow("Detected Objects", cv2.WINDOW_NORMAL)
# Open log file
log_file_path = "object_appearances.log"

print("Đang chạy...")
print("Time: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Initialize flag to track whether person is detected
person_detected = False
time_counter = 0
while cap.isOpened():
    # Read frame from the video
    ret, frame = cap.read()
    if not ret:
        break

    # Lấy thời gian hiện tại
    current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

    # Nếu đến đầu giây mới, thì xử lý khung hình
    if int(current_time) > time_counter:
        print("current time: ", int(current_time))
        print("time counter: ", time_counter)
        time_counter = int(current_time)
        # Update object localizer
        boxes, scores, class_ids = yolov8_detector(frame)
        # Check if person is detected
        if any(class_id == 0 and score > 0.5 for class_id, score in zip(class_ids, scores)):
            if not person_detected:
                # If person was not detected before, update flag and log start time
                person_detected = True
                start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            if person_detected:
                # If person was detected before but not anymore, update flag and log end time
                person_detected = False
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(log_file_path, "a") as log_file:
                    log_file.write(f"Phát hiện người từ {start_time} đến {end_time}\n")

        combined_img = yolov8_detector.draw_detections(frame)
        cv2.imshow("Detected Objects", combined_img)

    # Press key q to stop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
