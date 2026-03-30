# ---------------------------
# Transaction Model
# ---------------------------

from sqlalchemy import Column, Integer, String, Float, DateTime
from db.database import Base
from datetime import datetime


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, index=True)

    reference = Column(String, unique=True, index=True)

    phone = Column(String)
    country_iso = Column(String)

    amount = Column(Float, nullable=True)
    plan_id = Column(Integer, nullable=True)

    operator_id = Column(Integer, nullable=True)

    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)