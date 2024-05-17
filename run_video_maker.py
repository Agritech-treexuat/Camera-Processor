from processor.video_maker_processor import VideoMakerProcessor
from db_handler.mongodb_handler import MongoDBHandler
import schedule
import time

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

    db_handler = MongoDBHandler(mongo_uri, db_name)
    video_processor = VideoMakerProcessor(db_handler)
    schedule.every().day.at("23:39").do(video_processor.process_projects)
    # video_processor.process_projects()

     # Vòng lặp chạy lập lịch
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
