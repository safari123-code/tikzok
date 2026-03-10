from sqlalchemy import Column, Integer, String, DateTime
from db.database import Base
import datetime


class OtpChallenge(Base):
    __tablename__ = "otp_challenges"

    id = Column(Integer, primary_key=True)
    channel = Column(String)  # email / phone
    target = Column(String)
    otp_hash = Column(String)
    expires_at = Column(DateTime)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)