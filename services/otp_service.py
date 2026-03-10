# ---------------------------
# OTP Service — FINAL
# services/otp_service.py
# ---------------------------

import hmac
import secrets
import time


class OtpService:

    DEFAULT_TTL_SECONDS = 300  # 5 minutes

    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate secure numeric OTP"""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def constant_time_equals(a: str, b: str) -> bool:
        """Safe compare (anti timing attack)"""
        return hmac.compare_digest(a.encode(), b.encode())

    @staticmethod
    def now_ts() -> int:
        return int(time.time())

    @classmethod
    def expires_at(cls) -> int:
        return cls.now_ts() + cls.DEFAULT_TTL_SECONDS
    
    from services.redis_service import redis_client
import hashlib


class OtpService:

    TTL = 300
    MAX_ATTEMPTS = 5

    @staticmethod
    def store_otp(key: str, code: str):
        otp_hash = hashlib.sha256(code.encode()).hexdigest()
        redis_client.setex(key, OtpService.TTL, otp_hash)

    @staticmethod
    def verify_otp(key: str, entered_code: str):
        saved_hash = redis_client.get(key)
        if not saved_hash:
            return False

        entered_hash = hashlib.sha256(entered_code.encode()).hexdigest()
        return hmac.compare_digest(saved_hash, entered_hash)