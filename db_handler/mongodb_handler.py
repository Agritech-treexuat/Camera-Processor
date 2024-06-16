import pymongo
import threading
import time
from bson.objectid import ObjectId
from datetime import datetime, timedelta

class MongoDBHandler:
    def __init__(self, mongo_uri, db_name):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.load_rtsp_links()

    def insert_detection_log(self, camera_id, start_time, end_time, video_url):
        # Chuyển đổi chuỗi thành datetime
        start_time_date = datetime.strptime(start_time, "%Y-%m-%d_%H-%M-%S")
        end_time_date = datetime.strptime(end_time, "%Y-%m-%d_%H-%M-%S")
        log_data = {
            "camera_id": camera_id,
            "start_time": start_time_date,
            "end_time": end_time_date,
            "video_url": video_url
        }
        self.db.ObjectDetections.insert_one(log_data)
    
    def insert_connection_log(self, camera_id, start_time, end_time):
        start_time = datetime.strptime(start_time, '%Y-%m-%d_%H-%M-%S')
        end_time = datetime.strptime(end_time, '%Y-%m-%d_%H-%M-%S')
        log_data = {
            "camera_id": camera_id,
            "start_time": start_time,
            "end_time": end_time
        }
        self.db.ConnectionLosses.insert_one(log_data)

    def get_rtsp_links(self):
        links = []
        cursor = self.db.Cameras.find({}, {"_id": 0, "rtsp_link": 1})
        for document in cursor:
            links.append(document["rtsp_link"])
        return links

    def start_rtsp_links_watcher(self):
        def watch_rtsp_links():
            while True:
                # Lặp vô hạn để theo dõi thay đổi trong collection "Cameras"
                try:
                    # Kiểm tra thay đổi trong collection "Cameras"
                    camera_collection = self.db["Cameras"]
                    latest_change = camera_collection.find_one({}, sort=[('$natural', -1)])
                    if latest_change:
                        latest_change_time = latest_change['_id'].generation_time

                        if latest_change_time and (not self.last_change_time or latest_change_time > self.last_change_time):
                            print("Cập nhật danh sách RTSP URLs từ MongoDB...")
                            self.load_rtsp_links()
                            self.last_change_time = latest_change_time
                except Exception as e:
                    print(f"Lỗi khi kiểm tra thay đổi trong collection 'Cameras': {e}")
                
                # Chờ một khoảng thời gian trước khi kiểm tra lại
                time.sleep(10)

        self.last_change_time = None

        thread = threading.Thread(target=watch_rtsp_links)
        thread.start()
    def load_rtsp_links(self):
        self.rtsp_links = self.get_rtsp_links()

    def load_object_detection_by_date(self, date):
        # load all object detection logs of the day (start_time and end_time in that day)
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        # Tìm các tài liệu có start_time nằm trong khoảng thời gian này
        cursor = self.db.ObjectDetections.find({"start_time": {"$gte": start_of_day, "$lt": end_of_day}}, {"_id": 0})
        cursor_list = list(cursor)
        return cursor_list
    
    def load_connection_loss_by_date(self, date):
        # start of day is day at 0h0m0s, now date is datetime.date type
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        # Tìm các tài liệu có start_time nằm trong khoảng thời gian này
        cursor = self.db.ConnectionLosses.find({"start_time": {"$gte": start_of_day, "$lt": end_of_day}}, {"_id": 0})
        cursor_list = list(cursor)
        return cursor_list
    
    def get_cameraIndex_by_camera_id(self, camera_id):
        cursor = self.db.Cameras.find_one({"_id": ObjectId(camera_id)})
        return cursor["cameraIndex"]
    
    def update_object_detection_with_tx_hash_and_hash_by_date(self, date, tx_hash, concatenated_hash, date_timestamp, timeDescription, camera_id):
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        self.db.ObjectDetections.update_many({"camera_id": ObjectId(camera_id), "start_time": {"$gte": start_of_day, "$lt": end_of_day}}, {"$set": {"tx_hash": tx_hash, "concatenated_hash": concatenated_hash, "date_timestamp": date_timestamp, "timeDescription": timeDescription}})

    def update_connection_loss_with_tx_hash_and_concatenated_losses_by_date(self, date, tx_hash, concatenated_losses, total_loss_per_day, date_timestamp, camera_id):
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        self.db.ConnectionLosses.update_many({"camera_id": ObjectId(camera_id), "start_time": {"$gte": start_of_day, "$lt": end_of_day}}, {"$set": {"tx_hash": tx_hash, "concatenated_losses": concatenated_losses, "total_loss_per_day": total_loss_per_day, "date_timestamp": date_timestamp}})
    def update_image_info_with_tx_hash_and_hash_by_date(self, date_timestamp, tx_hash, image_hash, timeDescription, camera_id, capture_time):
        self.db.Images.update_many({"camera_id": ObjectId(camera_id), "capture_time": capture_time}, {"$set": {"tx_hash": tx_hash, "image_hash": image_hash, "timeDescription": timeDescription}})
        print("Update image info with tx_hash and hash by date")
    def get_projects_in_progress(self):
        projects = self.db.Projects.find({"status": "inProgress"})
        return projects

    def get_image_urls(self, camera_id, start_date):
        images = self.db.Images.find({"camera_id": ObjectId(camera_id), "capture_time": {"$gt": start_date}})
        image_urls = [image['image_url'] for image in images]
        return image_urls
    def insert_video_urls(self, projectId, video_urls):
        self.db.Projects.update_one({"_id": ObjectId(projectId)}, {"$set": {"video_urls": video_urls}})
    def insert_image(self, camera_id, capture_time, image_url):
        image_data = {
            "camera_id": ObjectId(camera_id),
            "capture_time": capture_time,
            "image_url": image_url
        }
        self.db.Images.insert_one(image_data)