import random
import hashlib
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Kết nối tới MongoDB
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collection
weather_collection = db['Weathers']
image_collection = db['Images']

def update_weather_description(district, start_time, end_time):
    # Điều kiện lọc các document weather cần cập nhật
    weather_filter = {
        "district": district,
        "time": {
            "$gte": start_time,
            "$lte": end_time
        }
    }
    
    # Nội dung cập nhật
    weather_update = {
        "$set": {
            "description": "Nắng to"
        }
    }
    
    # Thực hiện cập nhật
    result = weather_collection.update_many(weather_filter, weather_update)
    print(f"Matched {result.matched_count} documents and modified {result.modified_count} documents.")

# Hàm tạo tx_hash và image_hash giả
def fake_hash():
    return hashlib.sha256(str(random.random()).encode()).hexdigest()

# Hàm tạo dữ liệu thời tiết giả
def fake_weather():
    return {
        "description": random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"]),
        "temp": f"{random.randint(-10, 40)}°C",
        "humidity": f"{random.randint(10, 100)}%",
        "windSpeed": f"{random.randint(0, 20)} km/h"
    }

def seed_data(camera_id, start_time, end_time, district):
    current_time = start_time

    while current_time <= end_time:
        # Cập nhật document image có sẵn
        image_filter = {
            "camera_id": ObjectId(camera_id),
            "$expr": {
                "$and": [
                    {"$eq": [{"$year": "$capture_time"}, current_time.year]},
                    {"$eq": [{"$month": "$capture_time"}, current_time.month]},
                    {"$eq": [{"$dayOfMonth": "$capture_time"}, current_time.day]},
                    {"$eq": [{"$hour": "$capture_time"}, current_time.hour]}
                ]
            }
        }
        image_update = {
            "$set": {
                "tx_hash": fake_hash(),
                "image_hash": fake_hash()
            }
        }
        image_collection.update_one(image_filter, image_update)

        # Tạo document weather giả
        weather_data = {
            "district": district,
            "time": current_time,
            **fake_weather()
        }
        weather_collection.insert_one(weather_data)

        # Cập nhật thời gian hiện tại thêm 1 giờ
        current_time += timedelta(hours=1)

# Đầu vào
camera_id = "6635fb75f2303b5211710426"  # ID của camera
start_time = datetime(2024, 2, 1, 0, 0, 0)  # Thời gian bắt đầu
end_time = datetime(2024, 7, 1, 0, 0, 0)  # Thời gian kết thúc
district = "tây ninh"  # Tỉnh/quận

# Chạy hàm seed_data
seed_data(camera_id, start_time, end_time, district)

# Chạy hàm update_weather_description
# update_weather_description(district, start_time, end_time)
