import cv2
import threading
from datetime import datetime
from pymongo import MongoClient
from yolov8 import YOLOv8
from db_handler import MongoDBHandler
import time

class RTSPProcessor:
    def __init__(self, mongo_uri, db_name):
        self.rtsp_links = []
        self.yolov8_detector = YOLOv8("models/yolov8m.onnx", conf_thres=0.5, iou_thres=0.5)
        self.db_handler = MongoDBHandler(mongo_uri, db_name)
        self.load_rtsp_links()

    def load_rtsp_links(self):
        self.rtsp_links = self.db_handler.get_rtsp_links()
        print(f"Danh sách RTSP URLs: {self.rtsp_links}")

    def start_rtsp_links_watcher(self):
        def watch_rtsp_links():
            while True:
                # Lặp vô hạn để theo dõi thay đổi trong collection "Camera"
                try:
                    # Kiểm tra thay đổi trong collection "Camera"
                    camera_collection = self.db_handler.db["Camera"]
                    latest_change = camera_collection.find_one({}, sort=[('$natural', -1)])
                    if latest_change:
                        latest_change_time = latest_change['_id'].generation_time

                        if latest_change_time and (not self.last_change_time or latest_change_time > self.last_change_time):
                            print("Cập nhật danh sách RTSP URLs từ MongoDB here...")
                            self.load_rtsp_links()
                            self.last_change_time = latest_change_time
                            

                except Exception as e:
                    print(f"Lỗi khi kiểm tra thay đổi trong collection 'Camera': {e}")
                
                # Chờ một khoảng thời gian trước khi kiểm tra lại
                time.sleep(10)

        self.last_change_time = None

        thread = threading.Thread(target=watch_rtsp_links)
        thread.start()

    def log_detection(self, camera_id, start_time, end_time):
        self.db_handler.insert_detection_log(camera_id, start_time, end_time)
    
    def process_yolo(self, frame):
        boxes, scores, class_ids = self.yolov8_detector(frame)
        if any(class_id == 0 and score > 0.5 for class_id, score in zip(class_ids, scores )):
            return True
        return False

    def process_rtsp(self, rtsp_link):
        print(f"Bắt đầu xử lý luồng cho URL: {rtsp_link}")
        # Lấy camera_id từ MongoDB dựa trên rtsp_link
        camera_id = self.db_handler.db.Camera.find_one({"rtsp_link": rtsp_link}, {"_id": 1})["_id"]

        cap = cv2.VideoCapture(rtsp_link)

        person_detected = False
        time_counter = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

            if int(current_time) > time_counter:
                time_counter = int(current_time)
                if self.process_yolo(frame):
                    if not person_detected:
                        person_detected = True
                        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if person_detected:
                        person_detected = False
                        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.log_detection(camera_id, start_time, end_time)

        cap.release()
        print(f"Kết thúc xử lý luồng cho URL: {rtsp_link}")

    def start_processing(self):
        self.start_rtsp_links_watcher()

        threads = []
        for rtsp_link in self.rtsp_links:
            thread = threading.Thread(target=self.process_rtsp, args=(rtsp_link,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        while True:
            current_rtsp_links = self.rtsp_links.copy()  # Tạo bản sao của danh sách RTSP links hiện tại

            # Kiểm tra sự thay đổi trong danh sách RTSP links
            while current_rtsp_links == self.rtsp_links:
                time.sleep(5)  # Chờ một khoảng thời gian trước khi kiểm tra lại
            else:
                # Nếu có sự thay đổi, xóa tất cả các luồng hiện tại và bắt đầu lại từ đầu
                for thread in threads:
                    thread.join()  # Đợi cho tất cả các luồng hiện tại kết thúc
                    
                threads.clear()  # Xóa tất cả các luồng

                # Tạo lại các luồng cho các liên kết RTSP mới
                for rtsp_link in self.rtsp_links:
                    thread = threading.Thread(target=self.process_rtsp, args=(rtsp_link,))
                    thread.start()
                    threads.append(thread)


