from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.exceptions import TimeExhausted
from hexbytes import HexBytes

class BlockchainHandler:
    def __init__(self, contract_address, abi, public_key, private_key, provider_url):
        self.web3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract_address = contract_address
        self.contract_abi = abi
        self.private_key = private_key
        self.caller = public_key

        # Khởi tạo contract instance
        self.contract_instance = self.web3.eth.contract(address=self.contract_address, abi=self.contract_abi)

        self.Chain_id = self.web3.eth.chain_id

        # Thêm middleware để tự động ký và gửi giao dịch
        self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(self.private_key))

    def upload_video_hash(self, cameraIndex, video_hash, date_timestamp, timeDescription):
        # Ghi lên Blockchain video_hash, camera_id, và date_timestamp
        try:
            nonce = self.web3.eth.get_transaction_count(self.caller)

            # Call your function
            call_function = self.contract_instance.functions.addVideo(cameraIndex, video_hash, date_timestamp, timeDescription).build_transaction({"chainId": self.Chain_id, "from": self.caller, "nonce": nonce})

            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(call_function, private_key=self.private_key)

            # Send transaction
            send_tx = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(send_tx)

            print("Transaction receipt:", tx_receipt)
            return tx_receipt
        except TimeExhausted as e:
            print("Timeout while waiting for transaction receipt:", e)
            return None

    def upload_connection_losses(self, cameraIndex, concatenated_losses, total_loss_per_day, date_timestamp):
        # Ghi lên Blockchain concatenated_losses, total_loss_per_day, camera_id, và date_timestamp
        try:
            nonce = self.web3.eth.get_transaction_count(self.caller)

            # Call your function
            call_function = self.contract_instance.functions.addConnectionLoss(cameraIndex, date_timestamp, concatenated_losses, total_loss_per_day).build_transaction({"chainId": self.Chain_id, "from": self.caller, "nonce": nonce})

            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(call_function, private_key=self.private_key)

            # Send transaction
            send_tx = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for transaction receipt
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(send_tx)

            print("Transaction receipt:", tx_receipt)
            return tx_receipt
        except TimeExhausted as e:
            print("Timeout while waiting for transaction receipt:", e)
            return None
