from rtsp_processor import RTSPProcessor
from db_handler import MongoDBHandler

def main():
    # Thay đổi thông tin kết nối MongoDB tùy thuộc vào cấu hình của bạn
    mongo_uri = "mongodb://huy:12345678@127.0.0.1:27017"
    db_name = "AgriDB"

    rtsp_processor = RTSPProcessor(mongo_uri, db_name)
    rtsp_processor.start_processing()

if __name__ == "__main__":
    main()
