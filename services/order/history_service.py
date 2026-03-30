# ---------------------------
# History Service (DB VERSION)
# ---------------------------

from db.database import SessionLocal
from models.transaction import Transaction


class HistoryService:

    # ---------------------------
    # Get user history
    # ---------------------------
    @staticmethod
    def get_by_user(user_id):

        db = SessionLocal()

        try:
            return (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id)
                .order_by(Transaction.id.desc())
                .all()
            )
        finally:
            db.close()

    # ---------------------------
    # Count
    # ---------------------------
    @staticmethod
    def count(user_id):
        return len(HistoryService.get_by_user(user_id))

    # ---------------------------
    # Admin (all history)
    # ---------------------------
    @staticmethod
    def get_all():

        db = SessionLocal()

        try:
            return (
                db.query(Transaction)
                .order_by(Transaction.id.desc())
                .all()
            )
        finally:
            db.close()