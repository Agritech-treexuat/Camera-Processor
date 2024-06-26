import cv2
import threading
from datetime import datetime
from yolov8 import YOLOv8
from db_handler.mongodb_handler import MongoDBHandler
import time
import os
from random import randint
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
from processor.data_upload_blockchain_processer import DataProcessor
from datetime import datetime, timedelta, timezone
import urllib
import m3u8
import streamlink
from vidgear.gears import CamGear



load_dotenv(override=True)

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"

class RTSPProcessor:
    def __init__(self, frame_skip, mongo_uri, db_name, blockchain_handler=None):
        self.rtsp_links = []
        self.yolov8_detector = YOLOv8("models/yolov8m.onnx", conf_thres=0.5, iou_thres=0.5)
        self.db_handler = MongoDBHandler(mongo_uri, db_name)
        self.load_rtsp_links()
        self.frame_skip = frame_skip
        self.blockchain_handler = blockchain_handler
        self.data_processor = DataProcessor(self.db_handler, self.blockchain_handler)

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

    def log_detection(self, camera_id, start_time, end_time, video_url):
        self.db_handler.insert_detection_log(camera_id, start_time, end_time, video_url)
    
    def upload_video_to_cloudinary(self, video_path, camera_id, start_time, end_time):
        try:
            # Tải video lên Cloudinary
            response = cloudinary.uploader.upload_large(video_path, 
                resource_type="video",
                folder=f"detected_object/{camera_id}",  # Lưu vào thư mục detected_object trên Cloudinary
                public_id=f"{camera_id}_{start_time}_{end_time}",  # Tạo public_id dựa trên camera_id, start_time, và end_time
                chunk_size=6000000
            )
            print(f"Uploaded video {video_path} to Cloudinary")
            print("responce:", response)
            
            # Lấy URL của video từ response của Cloudinary
            video_url = response['secure_url']
            
            # Xóa video sau khi hoàn thành ghi và upload
            self.delete_video(video_path)
            print(f"Đã xóa video {video_path}")

            # Lưu thông tin phát hiện vào MongoDB
            self.log_detection(camera_id, start_time, end_time, video_url)
            print(f"Đã lưu thông tin phát hiện vào MongoDB")
        except Exception as e:
            print(f"Error uploading video to Cloudinary: {e}")

    def process_yolo(self, frame):
        boxes, scores, class_ids = self.yolov8_detector(frame)
        if any(class_id in [0, 1, 2, 3, 5, 6, 7] and score > 0.5 for class_id, score in zip(class_ids, scores )):
            return True
        return False

    def process_rtsp(self, rtsp_link):
        print(f"Bắt đầu xử lý luồng cho URL: {rtsp_link}")
        # Lấy camera_id từ MongoDB dựa trên rtsp_link
        camera_id = self.db_handler.db.Cameras.find_one({"rtsp_link": rtsp_link}, {"_id": 1})["_id"]

        connection_lost = False
        connection_lost_time = None

        while True:
            try:
                stream = CamGear(
                    source=rtsp_link,
                    stream_mode=True,
                    logging=True,
                ).start()
                if connection_lost:
                    reconnection_time = datetime.now()
                    self.db_handler.insert_connection_log(camera_id, connection_lost_time, reconnection_time)
                    print(f"Kết nối lại thành công với camera {rtsp_link} lúc {reconnection_time}")
                    connection_lost = False
                break
            except Exception as e:
                print(f"Lỗi khi mở luồng RTSP: {e}")
                if not connection_lost:
                    connection_lost = True
                    connection_lost_time = datetime.now()
                    print(f"Mất kết nối với camera {rtsp_link} lúc {connection_lost_time}")
                # Kiểm tra nếu đến cuối ngày mà vẫn không kết nối lại được
                if connection_lost:
                    current_time = datetime.now()
                    if current_time.hour == 23 and current_time.minute >= 50:
                        reconnection_time = current_time.replace(hour=23, minute=59, second=59)
                        self.db_handler.insert_connection_log(camera_id, connection_lost_time, reconnection_time)
                        print(f"Lưu thông tin mất kết nối cuối ngày cho camera {rtsp_link} từ {connection_lost_time} đến {reconnection_time}")
                        connection_lost = False
                time.sleep(600)  # Đợi 10 phút trước khi thử lại

        person_detected = False
        last_detection_time = None
        time_counter = 0
        start_time = None
        recording = False  # Biến cờ để theo dõi việc ghi video
        current_frame_count = 0
        connection_lost = False
        connection_lost_time = None
        continuous_connection_lost_time = None
        real_connection_loss = False

        while True:
            current_frame_count += 1
            if (current_frame_count % 1000 == 0):
                print(f"current_frame_count: {current_frame_count}")
            try:
                frame = stream.read()
            except Exception as e:
                print(f"Lỗi khi đọc frame từ luồng RTSP: {e}")
                frame = None

            # check for 'q' key if pressed
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            
            if frame is None:
                if not connection_lost:
                    print("current_frame_count:", current_frame_count)
                    connection_lost = True
                    connection_lost_time = datetime.now()  # Ghi thời điểm mất kết nối
                    continuous_connection_lost_time = datetime.now()  # Cập nhật thời gian mất kết nối liên tục
                    print(f"Mất kết nối với camera {rtsp_link} lúc {connection_lost_time}")
                else:
                    # Kiểm tra nếu đã mất kết nối liên tục trong 1 phút
                    elapsed_time_since_last_lost_connection = datetime.now() - continuous_connection_lost_time
                    if elapsed_time_since_last_lost_connection.total_seconds() > 60:
                        real_connection_loss = True

                continue
            else:
                connection_lost = False
                if real_connection_loss:
                    reconnection_time = datetime.now()  # Ghi thời điểm kết nối lại
                    print(f"Kết nối lại với camera {rtsp_link} lúc {reconnection_time}")
                    # Lưu thông tin mất kết nối vào collection ConnectionLoss
                    print("Lưu thông tin mất kết nối vào collection ConnectionLoss")
                    self.db_handler.insert_connection_log(camera_id, connection_lost_time, reconnection_time)
                    real_connection_loss = False
                    continuous_connection_lost_time = None  # Đặt lại thời gian mất kết nối liên tục

            # cv2.imshow("Output Frame", frame) 

            if self.process_yolo(frame):
                last_detection_time = datetime.now()  # Cập nhật thời gian phát hiện gần nhất
                if not person_detected:
                    person_detected = True
                    start_time = last_detection_time.strftime("%Y-%m-%d_%H-%M-%S")
                    recording = True  # Bắt đầu ghi video khi phát hiện người
                    print(f"Phát hiện người tại {rtsp_link} lúc {start_time}")
            else:
                # Kiểm tra nếu đã vượt quá 1 phút kể từ lần cuối cùng phát hiện người
                if person_detected and last_detection_time is not None:
                    elapsed_time_since_last_detection = datetime.now() - last_detection_time
                    if elapsed_time_since_last_detection.total_seconds() > 60:
                        person_detected = False
                        print(f"Ngừng phát hiện người tại {rtsp_link} with time {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        end_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        if recording:
                            out.release()  # Đảm bảo rằng video cuối cùng được đóng sau khi kết thúc luồng
                        recording = False  # Dừng ghi video khi không phát hiện nữa
                        # Upload video phát hiện lên Cloudinary
                        upload_thread = threading.Thread(target=self.upload_video_to_cloudinary, args=(video_path, camera_id, start_time, end_time))
                        upload_thread.start()

            if recording:
                # Ghi video nếu đang trong trạng thái ghi
                if start_time is not None:
                    video_path = f"./detected_videos/{camera_id}_{start_time}.avi"
                    if not os.path.exists(os.path.dirname(video_path)):
                        os.makedirs(os.path.dirname(video_path))  # Tạo thư mục nếu chưa tồn tại
                    
                    if not os.path.exists(video_path):
                        fourcc = cv2.VideoWriter_fourcc(*'XVID')
                        out = cv2.VideoWriter(video_path, fourcc, 30 / self.frame_skip, (frame.shape[1], frame.shape[0]))
                    
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

    def capture_and_upload_image(self, rtsp_link):
        while True:
            # Tính toán thời điểm chụp ảnh ngẫu nhiên trong mỗi giờ
            current_time = datetime.now()
            next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            random_minute = randint(0, 59)
            capture_time = next_hour.replace(minute=random_minute)

            # capture_time = current_time + timedelta(seconds=10)
            print(f"Thời gian hiện tại: {current_time}")
            print(f"Chờ đến thời điểm chụp ảnh: {capture_time}")

            # Chờ đến thời điểm chụp ảnh
            while datetime.now() < capture_time:
                time.sleep(1)

            try:
                # Chụp frame tại thời điểm đã chọn từ luồng RTSP
                stream = CamGear(
                    source=rtsp_link,
                    stream_mode=True,
                    logging=True,
                ).start()
                frame = stream.read()
                stream.stop()
                if frame is None:
                    print(f"Lỗi khi chụp frame từ {rtsp_link}")
                    # try to read the next 5 frame
                    for i in range(5):
                        stream = CamGear(
                            source=rtsp_link,
                            stream_mode=True,
                            logging=True,
                        ).start()
                        frame = stream.read()
                        stream.stop()
                        if frame is not None:
                            break
                        time.sleep(1)
                if frame is None:
                    print(f"Lỗi khi chụp frame từ {rtsp_link} for 5 times")
                    continue
                # cap = cv2.VideoCapture(rtsp_link, cv2.CAP_FFMPEG)
                # ret, frame = cap.read()
                # cap.release()
                # if not ret:
                #     print(f"Lỗi khi chụp frame từ {rtsp_link}")
                #     continue
            except Exception as e:
                print(f"Lỗi khi chụp frame từ {rtsp_link}: {e}")
                continue

            # Tạo tên file ảnh dựa trên thời gian chụp và camera ID
            camera_id = self.db_handler.db.Cameras.find_one({"rtsp_link": rtsp_link}, {"_id": 1})["_id"]
            image_filename = f"{camera_id}_{capture_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"

            if not os.path.exists("./temp_images"):
                os.makedirs("./temp_images")
            # Lưu ảnh vào thư mục tạm thời
            temp_image_path = os.path.join("./temp_images", image_filename)
            cv2.imwrite(temp_image_path, frame)

            try:
                # Upload image to Cloudinary
                response = cloudinary.uploader.upload(temp_image_path, 
                    folder=f"captured_images/{camera_id}",  # Save image to captured_images folder on Cloudinary
                    public_id=image_filename,  # Use image filename as public_id
                )
                print(f"Uploaded image {image_filename} to Cloudinary")

                # Get image URL from Cloudinary response
                image_url = response['secure_url']

                # Save image info to MongoDB
                image_info = {
                    "camera_id": camera_id,
                    "capture_time": capture_time,
                    "image_url": image_url
                }
                self.db_handler.db.Images.insert_one(image_info)
                print("Saved image info to MongoDB")
                try:
                    # Process and upload image to Blockchain
                    self.data_processor.process_image_and_upload_to_blockchain(frame, image_info)
                except Exception as e:
                    print(f"Error processing and uploading image to Blockchain: {e}")
            except Exception as e:
                print(f"Error uploading image to Cloudinary: {e}")

            # Xóa ảnh tạm sau khi upload
            os.remove(temp_image_path)

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
    
    def start_capture_and_upload_threads(self):
        threads = []
        for rtsp_link in self.rtsp_links:
            thread = threading.Thread(target=self.capture_and_upload_image, args=(rtsp_link,))
            thread.start()
            threads.append(thread)
        return threads
    
    def extract_and_upload_frames(self, video_path, camera_id):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / 24)  # Lấy 24 frame mỗi giây

        frame_count = 0
        start_date = datetime(2024, 5, 19)  # Specify the desired start date
        current_time = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = timedelta(hours=1)  # Each frame will represent a time point within a day

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # Tạo tên file ảnh dựa trên thời gian chụp và camera ID
                image_filename = f"{camera_id}_{current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                temp_image_path = os.path.join("./temp_images", image_filename)
                
                if not os.path.exists("./temp_images"):
                    os.makedirs("./temp_images")

                # Lưu frame vào thư mục tạm thời
                cv2.imwrite(temp_image_path, frame)

                try:
                    # Upload image to Cloudinary
                    response = cloudinary.uploader.upload(temp_image_path, 
                        folder=f"captured_images/{camera_id}",
                        public_id=image_filename,
                    )
                    print(f"Uploaded image {image_filename} to Cloudinary")

                    # Get image URL from Cloudinary response
                    image_url = response['secure_url']

                    # Save image info to MongoDB
                    self.db_handler.insert_image(camera_id, current_time, image_url)
                    print("Saved image info to MongoDB")
                except Exception as e:
                    print(f"Error uploading image to Cloudinary: {e}")
                
                # Xóa ảnh tạm sau khi upload
                os.remove(temp_image_path)

                # Tăng thời gian cho khung hình tiếp theo
                current_time += delta

            frame_count += 1
        
        cap.release()
        print("Finished processing video.")