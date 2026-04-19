import logging
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = logging.getLogger(__name__)

class Wallet:
    def __init__(self, private_key_hex: Optional[str] = None):
        if private_key_hex:
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
        
        self.public_key = self.private_key.public_key()
        self.address = self.public_key.public_bytes_raw().hex()
        logger.info(f"Wallet initialized with address: {self.address}")

    def sign_transaction(self, data: bytes) -> str:
        signature = self.private_key.sign(data)
        return signature.hex()

    def get_public_key_hex(self) -> str:
        return self.public_key.public_bytes_raw().hex()

    async def pay(self, amount: float, destination: str) -> bool:
        # Placeholder for actual payment API (Stripe, Coinbase, etc.)
        logger.info(f"Mock payment of {amount} to {destination}")
        return True
