from sqlalchemy import Column, Integer, String, DateTime, Boolean
from db.database import Base
from datetime import datetime, timedelta


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id = Column(Integer, primary_key=True)

    # email ou phone
    channel = Column(String, nullable=False)  # "email" ou "phone"
    target = Column(String, index=True, nullable=False)

    # 🔐 stocker hash du code (pas le code brut)
    otp_hash = Column(String, nullable=False)

    # sécurité
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)

    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ---------------------------
    # Expiration helper
    # ---------------------------
    @staticmethod
    def generate_expiry(minutes=5):
        return datetime.utcnow() + timedelta(minutes=minutes)