# ---------------------------
# User Model
# ---------------------------

from sqlalchemy import Column, Integer, String, DateTime
from db.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)

    name = Column(String, nullable=True)

    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)

    # ---------------------------
    # Helper (optionnel)
    # ---------------------------
    def __repr__(self):
        return f"<User id={self.id} email={self.email} phone={self.phone}>"