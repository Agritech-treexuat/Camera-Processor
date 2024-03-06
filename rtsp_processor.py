import cv2
import threading
from datetime import datetime
from pymongo import MongoClient
from yolov8 import YOLOv8
from db_handler import MongoDBHandler
import time
import os
import boto3

class RTSPProcessor:
    def __init__(self, frame_skip, mongo_uri, db_name, WASABI_ACCESS_KEY, WASABI_SECRET_KEY, WASABI_REGION, WASABI_ENDPOINT_URL, WASABI_BUCKET_NAME):
        self.rtsp_links = []
        self.yolov8_detector = YOLOv8("models/yolov8m.onnx", conf_thres=0.5, iou_thres=0.5)
        self.db_handler = MongoDBHandler(mongo_uri, db_name)
        self.load_rtsp_links()
        self.wasabi_client = boto3.client(
            's3',
            endpoint_url=WASABI_ENDPOINT_URL,
            aws_access_key_id=WASABI_ACCESS_KEY,
            aws_secret_access_key=WASABI_SECRET_KEY,
            region_name=WASABI_REGION
        )
        self.wasabi_bucket_name = WASABI_BUCKET_NAME
        self.frame_skip = frame_skip

    def load_rtsp_links(self):
        self.rtsp_links = self.db_handler.get_rtsp_links()
        print(f"Danh sách RTSP URLs: {self.rtsp_links}")

    def start_rtsp_links_watcher(self):
        def watch_rtsp_links():
            while True:
                # Lặp vô hạn để theo dõi thay đổi trong collection "Cameras"
                try:
                    # Kiểm tra thay đổi trong collection "Cameras"
                    camera_collection = self.db_handler.db["Cameras"]
                    latest_change = camera_collection.find_one({}, sort=[('$natural', -1)])
                    if latest_change:
                        latest_change_time = latest_change['_id'].generation_time

                        if latest_change_time and (not self.last_change_time or latest_change_time > self.last_change_time):
                            print("Cập nhật danh sách RTSP URLs từ MongoDB here...")
                            self.load_rtsp_links()
                            self.last_change_time = latest_change_time
                            

                except Exception as e:
                    print(f"Lỗi khi kiểm tra thay đổi trong collection 'Cameras': {e}")
                
                # Chờ một khoảng thời gian trước khi kiểm tra lại
                time.sleep(10)

        self.last_change_time = None

        thread = threading.Thread(target=watch_rtsp_links)
        thread.start()

    def log_detection(self, camera_id, start_time, end_time):
        self.db_handler.insert_detection_log(camera_id, start_time, end_time)
    
    def upload_video_to_wasabi(self, video_path, camera_id, start_time, end_time):
        try:
            file_name = os.path.basename(video_path)
            wasabi_key = f"detected_videos/{camera_id}/{start_time}_{end_time}_{file_name}"
            self.wasabi_client.upload_file(video_path, self.wasabi_bucket_name, wasabi_key)
            print(f"Uploaded video {file_name} to Wasabi")
            self.delete_video(video_path)  # Xóa video sau khi hoàn thành ghi và upload
            print(f"Đã xóa video {video_path}")
        except Exception as e:
            print(f"Error uploading video to Wasabi: {e}")

    def process_yolo(self, frame):
        boxes, scores, class_ids = self.yolov8_detector(frame)
        if any(class_id == 0 and score > 0.5 for class_id, score in zip(class_ids, scores )):
            return True
        return False

    def process_rtsp(self, rtsp_link):
        print(f"Bắt đầu xử lý luồng cho URL: {rtsp_link}")
        # Lấy camera_id từ MongoDB dựa trên rtsp_link
        camera_id = self.db_handler.db.Cameras.find_one({"rtsp_link": rtsp_link}, {"_id": 1})["_id"]

        cap = cv2.VideoCapture(rtsp_link)

        person_detected = False
        time_counter = 0
        start_time = None
        recording = False  # Biến cờ để theo dõi việc ghi video
        current_frame_count = 0

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
                        start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        recording = True  # Bắt đầu ghi video khi phát hiện người
                else:
                    if person_detected:
                        person_detected = False
                        end_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        if recording:
                            out.release()  # Đảm bảo rằng video cuối cùng được đóng sau khi kết thúc luồng
                            
                        recording = False  # Dừng ghi video khi không phát hiện nữa
                        # Upload video phát hiện lên Wasabi
                        upload_thread = threading.Thread(target=self.upload_video_to_wasabi, args=(video_path, camera_id, start_time, end_time))
                        upload_thread.start()

            if recording:
                # Ghi video nếu đang trong trạng thái ghi
                if start_time is not None:
                    video_path = f"./detected_videos/{camera_id}_{start_time}.mp4"
                    if not os.path.exists(os.path.dirname(video_path)):
                        os.makedirs(os.path.dirname(video_path))  # Tạo thư mục nếu chưa tồn tại
                    if not os.path.exists(video_path):
                        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 30 / self.frame_skip, (frame.shape[1], frame.shape[0]))
                    
                    if current_frame_count % self.frame_skip == 0:
                        out.write(frame)
                    current_frame_count += 1
        
        

        cap.release()
        print(f"Kết thúc xử lý luồng cho URL: {rtsp_link}")

    def delete_video(self, video_path):
        try:
            os.remove(video_path)
            print(f"Đã xóa video: {video_path}")
        except Exception as e:
            print(f"Lỗi khi xóa video: {e}")

    def compress_video(self, video_path):
        # Đọc video gốc
        cap = cv2.VideoCapture(video_path)

        # Khởi tạo VideoWriter cho video nén
        compressed_video_path = video_path.replace('.mp4', '_compressed.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Sử dụng codec H.264
        out = cv2.VideoWriter(compressed_video_path, fourcc, 30, (int(cap.get(3)), int(cap.get(4))))

        # Nén video frame by frame
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        # Giải phóng tài nguyên
        cap.release()
        out.release()

        # Xóa video gốc
        os.remove(video_path)

        # Đổi tên video nén thành tên gốc
        os.rename(compressed_video_path, video_path)

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
