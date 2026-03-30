# ---------------------------
# Auth Service (User)
# ---------------------------

from db.database import SessionLocal
from models.user import User


# ---------------------------
# Get or Create User
# ---------------------------
def get_or_create_user(email=None, phone=None):

    db = SessionLocal()

    try:
        # ---------------------------
        # Find user
        # ---------------------------
        if email:
            user = db.query(User).filter(User.email == email).first()
        elif phone:
            user = db.query(User).filter(User.phone == phone).first()
        else:
            return None

        # ---------------------------
        # Create user if not exists
        # ---------------------------
        if not user:
            user = User(
                email=email,
                phone=phone
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    finally:
        db.close()