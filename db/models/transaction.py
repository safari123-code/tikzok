# ---------------------------
# Transaction Model (PRO SAFE)
# ---------------------------

from sqlalchemy import Column, Integer, String, DateTime, Numeric
from db.database import Base
from datetime import datetime


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, nullable=False, index=True)

    reference = Column(String, unique=True, nullable=False, index=True)

    phone = Column(String, nullable=False)
    country_iso = Column(String)

    amount = Column(Numeric(10, 2), nullable=False)

    plan_id = Column(Integer)
    operator_id = Column(Integer)

    status = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )