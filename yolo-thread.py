import cv2
from yolov8 import YOLOv8
from datetime import datetime
import threading

# Đọc danh sách URL RTSP từ tệp cấu hình
with open("rtsp_urls.txt", "r") as file:
    rtsp_urls = file.readlines()
rtsp_urls = [url.strip() for url in rtsp_urls]

# Khởi tạo bộ nhận diện YOLOv7
model_path = "models/yolov8m.onnx"
yolov8_detector = YOLOv8(model_path, conf_thres=0.5, iou_thres=0.5)

# Đường dẫn tệp nhật ký
log_file_path = "object_appearances.log"

def process_yolo(frame):
    boxes, scores, class_ids = yolov8_detector(frame)
    # Kiểm tra xem có phát hiện người không
    if any(class_id == 0 and score > 0.5 for class_id, score in zip(class_ids, scores)):
        return True
    return False

def log_to_db(start_time, end_time, camera_url):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Phát hiện người từ {start_time} đến {end_time} trên camera {camera_url}\n")
        print(f"Phát hiện người từ {start_time} đến {end_time} trên camera {camera_url}\n")

def process_rtsp(rtsp_url):
    print(f"Bắt đầu xử lý luồng cho URL: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)

    person_detected = False
    time_counter = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

        if int(current_time) > time_counter:
            time_counter = int(current_time)
            if process_yolo(frame):
                if not person_detected:
                    person_detected = True
                    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                if person_detected:
                    person_detected = False
                    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_to_db(start_time, end_time, rtsp_url)

    cap.release()
    print(f"Kết thúc xử lý luồng cho URL: {rtsp_url}")

def main():
    print("Đang chạy...")
    print("Time: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Tạo các luồng cho mỗi URL RTSP
    threads = []
    for rtsp_url in rtsp_urls:
        thread = threading.Thread(target=process_rtsp, args=(rtsp_url,))
        thread.start()
        threads.append(thread)

    # Chờ tất cả các luồng hoàn thành
    for thread in threads:
        thread.join()

    print("Kết thúc chương trình.")

if __name__ == "__main__":
    main()
