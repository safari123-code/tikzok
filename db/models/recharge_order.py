from sqlalchemy import Column, Integer, String, Float, DateTime
from db.database import Base
import datetime


class RechargeOrder(Base):
    __tablename__ = "recharge_orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    beneficiary_phone = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String, default="pending")
    idempotency_key = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)