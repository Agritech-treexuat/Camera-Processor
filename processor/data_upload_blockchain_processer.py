import hashlib
import time
from datetime import datetime
import requests

class DataProcessor:
    def __init__(self, mongo_handler, blockchain_handler):
        self.mongo_handler = mongo_handler
        self.blockchain_handler = blockchain_handler

    def process_data_and_upload_to_blockchain(self):
        # Lấy ngày hôm nay
        current_date = datetime.now().date()
        # current date = 5/5
        # current_date = datetime.strptime("2024-05-06", "%Y-%m-%d")

        # Lấy dữ liệu ObjectDetections của ngày hôm nay
        object_detections = self.mongo_handler.load_object_detection_by_date(current_date)

        # Lấy dữ liệu ConnectionLoss của ngày hôm nay
        connection_losses = self.mongo_handler.load_connection_loss_by_date(current_date)

        # Sắp xếp lại dữ liệu theo camera_id
        object_detections_by_camera = {}

        for detection in object_detections:
            camera_id = detection["camera_id"]
            cameraIndex = self.mongo_handler.get_cameraIndex_by_camera_id(camera_id)
            if cameraIndex not in object_detections_by_camera:
                object_detections_by_camera[cameraIndex] = []
            object_detections_by_camera[cameraIndex].append(detection)

        connection_losses_by_camera = {}
        for loss in connection_losses:
            camera_id = loss["camera_id"]
            cameraIndex = self.mongo_handler.get_cameraIndex_by_camera_id(camera_id)
            if cameraIndex not in connection_losses_by_camera:
                connection_losses_by_camera[cameraIndex] = []
            connection_losses_by_camera[cameraIndex].append(loss)

        # print("Object detections by camera:", object_detections_by_camera)
        # Xử lý dữ liệu và ghi lên Blockchain cho từng camera
        for cameraIndex, detections in object_detections_by_camera.items():
            # Tải video từ video_url và ghép nối lại
            concatenated_hash = ""
            timeDescription = ""
            for detection in detections:
                # Lấy video_url từ detection
                video_url = detection.get('video_url')
                start_time = detection.get('start_time')
                end_time = detection.get('end_time')
                timeDescription += f"Start Time: {start_time}, End Time: {end_time}"
                camera_id = detection.get('camera_id')
                if video_url:
                    # Tải xuống video từ URL
                    video_content = self.download_video(video_url)
                    if video_content:
                        # Hash nội dung video
                        video_hash = self.hash_video(video_content)
                        concatenated_hash += video_hash  # Nối hash vào chuỗi kết quả


            # Convert ngày thành Unix timestamp
            date_timestamp = int(datetime.timestamp(datetime.now()))

            print("Ghi lên Blockchain: ", cameraIndex, concatenated_hash, date_timestamp, timeDescription)
            

            # Ghi lên Blockchain
            tx_receipt = self.blockchain_handler.upload_video_hash(cameraIndex, concatenated_hash, date_timestamp, timeDescription)
            if tx_receipt:
                # Lấy transaction hash (string) từ tx_receipt 
                tx_hash = tx_receipt['transactionHash'].hex()
                print("Transaction hash:", tx_hash)
                # update all detections with tx_hash and concatenated_hash in that date
                try:
                    self.mongo_handler.update_object_detection_with_tx_hash_and_hash_by_date(current_date, tx_hash, concatenated_hash, date_timestamp, timeDescription, camera_id)
                    print("Updated object detection with tx_hash and concatenated_hash")
                except Exception as e:
                    print("Error while updating object detection with tx_hash and concatenated_hash:", str(e))
            else:
                print("Không thể ghi video lên Blockchain")
        print("Kết thúc xử lý ObjectDetections")

        # print("Connection losses by camera:", connection_losses_by_camera)
        # Xử lý dữ liệu và ghi lên Blockchain cho từng camera về ConnectionLoss
        for cameraIndex, losses in connection_losses_by_camera.items():
            # Ghép nối lại các khoảng thời gian start_time và end_time
            concatenated_losses, total_loss_per_day = self.concatenate_connection_losses(losses)
            camera_id = losses[0].get('camera_id')

            # Convert ngày thành Unix timestamp
            date_timestamp = int(datetime.timestamp(datetime.now()))

            print("Ghi lên Blockchain: ", cameraIndex, concatenated_losses, total_loss_per_day, date_timestamp)
            
            # Ghi lên Blockchain
            tx_receipt = self.blockchain_handler.upload_connection_losses(cameraIndex, concatenated_losses, total_loss_per_day, date_timestamp)
            if tx_receipt:
                # Lấy transaction hash (string) từ tx_receipt 
                tx_hash = tx_receipt['transactionHash'].hex()
                print("Transaction hash:", tx_hash)
                # update all losses with tx_hash and concatenated_losses in that date
                try:
                    self.mongo_handler.update_connection_loss_with_tx_hash_and_concatenated_losses_by_date(current_date, tx_hash, concatenated_losses, total_loss_per_day, date_timestamp, camera_id)
                    print("Updated connection losses with tx_hash and concatenated_losses")
                except Exception as e:
                    print("Error while updating connection losses with tx_hash and concatenated_losses:", str(e))
            else:
                print("Không thể ghi connection losses lên Blockchain")
        print("Kết thúc xử lý ConnectionLosses")

    def process_image_and_upload_to_blockchain(self, frame, image_info):
        camera_id = image_info["camera_id"]
        capture_time = image_info["capture_time"]
        cameraIndex = self.mongo_handler.get_cameraIndex_by_camera_id(camera_id)
        image_hash = self.hash_image(frame)
        date_timestamp = int(datetime.timestamp(datetime.now()))
        timeDescription = f"Capture at Time: {image_info['capture_time']}"

        # Ghi lên Blockchain
        tx_receipt = self.blockchain_handler.upload_image_hash(cameraIndex, image_hash, date_timestamp, timeDescription)
        if tx_receipt:
            # Lấy transaction hash (string) từ tx_receipt 
            tx_hash = tx_receipt['transactionHash'].hex()
            # update all losses with tx_hash and concatenated_losses in that date
            self.mongo_handler.update_image_info_with_tx_hash_and_hash_by_date(date_timestamp, tx_hash, image_hash, timeDescription, camera_id, capture_time)
        else:
            print("Không thể ghi image lên Blockchain")

    def hash_video(self, video_data):
        # Hash video_data và trả về hash
        hash_object = hashlib.sha256(video_data)
        return hash_object.hexdigest()
    
    def hash_image(self, image_data):
        # Hash image_data và trả về hash
        hash_object = hashlib.sha256(image_data)
        return hash_object.hexdigest()
    
    def download_video(self, video_url):
        try:
            # Tải xuống video từ URL
            response = requests.get(video_url)
            if response.status_code == 200:
                return response.content
            else:
                print("Không thể tải xuống video. Mã trạng thái:", response.status_code)
                return None
        except Exception as e:
            print("Đã xảy ra lỗi khi tải xuống video:", str(e))
            return None

    def concatenate_connection_losses(self, losses):
        concatenated_losses = ''
        total_loss_per_day = 0

        # Kiểm tra xem losses có dữ liệu không
        if len(losses) == 0:
            return concatenated_losses, total_loss_per_day

        # Lấy ngày của losses đầu tiên
        date = losses[0]['start_time'].date()

        # Lặp qua từng mất kết nối
        for loss in losses:
            start_time = loss['start_time']
            end_time = loss['end_time']

            # Tính thời gian mất kết nối và cộng vào tổng thời gian mất kết nối của ngày đó
            loss_duration = (end_time - start_time).total_seconds()
            total_loss_per_day += loss_duration

            # Ghép nối các mất kết nối vào chuỗi concatenated_losses
            concatenated_losses += f"Start Time: {start_time}, End Time: {end_time}, Duration: {loss_duration} seconds\n"
        
        total_loss_per_day = int(total_loss_per_day)

        return concatenated_losses, total_loss_per_day

