from db_handler.mongodb_handler import MongoDBHandler
from dotenv import load_dotenv
import os

import schedule
import time
from db_handler.blockchain_handler import BlockchainHandler
from processor.data_upload_blockchain_processer import DataProcessor

from constants import abi

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

    mongo_handler = MongoDBHandler(mongo_uri, db_name)

    # 3. Hash and upload to Blockchain
    # Kết nối với smart contract thông qua contract address và abi00000000
    contract_address = os.getenv("VIDEO_CONTRACT_ADDRESS")
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    public_key = os.getenv("WALLET_PUBLIC_KEY")
    provider_url = os.getenv("PROVIDER_URL")


    blockchain_handler = BlockchainHandler(contract_address, abi, public_key, private_key, provider_url)
    data_processor = DataProcessor(mongo_handler, blockchain_handler)

    # Lập lịch cho công việc chạy vào 12h đêm mỗi ngày
    # schedule.every().day.at("22:25").do(data_processor.process_data_and_upload_to_blockchain)
    print("Start processing data and upload to blockchain")
    data_processor.process_data_and_upload_to_blockchain()

    # Vòng lặp chạy lập lịch
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
