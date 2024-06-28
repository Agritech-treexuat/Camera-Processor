from processor.rtsp_processor import RTSPProcessor
from db_handler.mongodb_handler import MongoDBHandler
from dotenv import load_dotenv
import os

load_dotenv(override=True)

def main():
    # Thay đổi thông tin kết nối MongoDB tùy thuộc vào cấu hình của bạn

    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_PORT = os.getenv("MONGO_PORT")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

    MONGO_URI = os.getenv("MONGO_URI")

    mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
    if MONGO_URI:
        mongo_uri = MONGO_URI
    print(f"Connecting to MongoDB...")
    db_name = MONGO_DB_NAME
    frame_skip = 10
    
    # 1. RTSP Processor
    rtsp_processor = RTSPProcessor(frame_skip, mongo_uri, db_name)
    rtsp_processor.extract_and_upload_frames('./video_farm.mp4', '66544897e7f65e05a4bb1e0c')

if __name__ == "__main__":
    main()
