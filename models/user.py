from sqlalchemy import Column, Integer, String, DateTime
from db.database import Base
import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)