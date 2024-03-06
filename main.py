from rtsp_processor import RTSPProcessor
from db_handler import MongoDBHandler
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    # Thay đổi thông tin kết nối MongoDB tùy thuộc vào cấu hình của bạn

    MONGO_USERNAME = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
    MONGO_HOST = os.getenv("MONGO_HOST")
    MONGO_PORT = os.getenv("MONGO_PORT")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

    WASABI_ACCESS_KEY = os.getenv("WASABI_ACCESS_KEY")
    WASABI_SECRET_KEY = os.getenv("WASABI_SECRET_KEY")
    WASABI_REGION = os.getenv("WASABI_REGION")
    WASABI_ENDPOINT_URL = os.getenv("WASABI_ENDPOINT_URL")
    WASABI_BUCKET_NAME = os.getenv("WASABI_BUCKET_NAME")

    mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
    db_name = MONGO_DB_NAME

    rtsp_processor = RTSPProcessor(mongo_uri, db_name, WASABI_ACCESS_KEY, WASABI_SECRET_KEY, WASABI_REGION, WASABI_ENDPOINT_URL, WASABI_BUCKET_NAME)
    rtsp_processor.start_processing()

if __name__ == "__main__":
    main()
