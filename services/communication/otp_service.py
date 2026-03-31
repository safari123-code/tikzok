# ---------------------------
# OTP Service (NO REDIS — SAFE)
# ---------------------------

import hmac
import secrets

# stockage temporaire mémoire (OK pour dev)
_memory_store = {}


class OtpService:

    TTL = 300

    @staticmethod
    def generate_code(length: int = 6) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def build_key(channel: str, target: str) -> str:
        return f"{channel}:{target}"

    @classmethod
    def store_otp(cls, channel: str, target: str, code: str):
        key = cls.build_key(channel, target)
        _memory_store[key] = code

    @classmethod
    def verify_otp(cls, channel: str, target: str, entered_code: str) -> bool:
        key = cls.build_key(channel, target)

        saved = _memory_store.get(key)
        if not saved:
            return False

        if hmac.compare_digest(saved, entered_code):
            del _memory_store[key]
            return True

        return False