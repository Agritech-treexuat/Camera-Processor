import cv2
from yolov8 import YOLOv8
from datetime import datetime

# # List of RTSP stream URLs
# rtsp_urls = [
#     "rtsp://username:password@ip_address1:port_number1/stream",
#     "rtsp://username:password@ip_address2:port_number2/stream",
#     # Add more RTSP URLs as needed
# ]

# Read RTSP URLs from a configuration file
with open("rtsp_urls.txt", "r") as file:
    rtsp_urls = file.readlines()
rtsp_urls = [url.strip() for url in rtsp_urls]
# Initialize YOLOv7 object detector
model_path = "models/yolov8m.onnx"
yolov8_detector = YOLOv8(model_path, conf_thres=0.5, iou_thres=0.5)

# Open log file
log_file_path = "object_appearances.log"

def process_yolo(frame):
    boxes, scores, class_ids = yolov8_detector(frame)
    # Check if person is detected
    if any(class_id == 0 and score > 0.5 for class_id, score in zip(class_ids, scores)):
        return True

    return False

def log_to_db(start_time, end_time, camera_url):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Phát hiện người từ {start_time} đến {end_time} trên camera {camera_url}\n")
        print(f"Phát hiện người từ {start_time} đến {end_time} trên camera {camera_url}\n")

def main():
    print("Đang chạy...")
    print("Time: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    person_detected = {url: False for url in rtsp_urls}
    time_counter = {url: 0 for url in rtsp_urls}

    for rtsp_url in rtsp_urls:
        cap = cv2.VideoCapture(rtsp_url)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

            if int(current_time) > time_counter[rtsp_url]:
                time_counter[rtsp_url] = int(current_time)
                if process_yolo(frame):
                    if not person_detected[rtsp_url]:
                        person_detected[rtsp_url] = True
                        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if person_detected[rtsp_url]:
                        person_detected[rtsp_url] = False
                        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_to_db(start_time, end_time, rtsp_url)

                # cv2.imshow("Detected Objects", frame)
                # combined_img = yolov8_detector.draw_detections(frame)
                # cv2.imshow("Detected Objects", combined_img)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()