# ---------------------------
# OTP Service (Redis + SMS/Email Ready)
# ---------------------------

import hmac
import secrets
import hashlib

from services.core.redis_service import redis_client


class OtpService:

    TTL = 300  # 5 minutes
    MAX_ATTEMPTS = 5

    # ---------------------------
    # Generate OTP
    # ---------------------------
    @staticmethod
    def generate_code(length: int = 6) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(length))

    # ---------------------------
    # Hash OTP
    # ---------------------------
    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    # ---------------------------
    # Build Redis Key
    # ---------------------------
    @staticmethod
    def build_key(channel: str, target: str) -> str:
        return f"otp:{channel}:{target}"

    # ---------------------------
    # Store OTP
    # ---------------------------
    @classmethod
    def store_otp(cls, channel: str, target: str, code: str):
        key = cls.build_key(channel, target)

        data = {
            "hash": cls.hash_code(code),
            "attempts": 0
        }

        redis_client.setex(key, cls.TTL, str(data))

    # ---------------------------
    # Verify OTP
    # ---------------------------
    @classmethod
    def verify_otp(cls, channel: str, target: str, entered_code: str) -> bool:
        key = cls.build_key(channel, target)

        raw = redis_client.get(key)
        if not raw:
            return False

        data = eval(raw.decode())

        # brute force protection
        if data["attempts"] >= cls.MAX_ATTEMPTS:
            redis_client.delete(key)
            return False

        entered_hash = cls.hash_code(entered_code)

        if hmac.compare_digest(data["hash"], entered_hash):
            redis_client.delete(key)  # one-time use
            return True

        # increment attempts
        data["attempts"] += 1
        redis_client.setex(key, cls.TTL, str(data))

        return False