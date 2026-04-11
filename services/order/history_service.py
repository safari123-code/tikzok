# ---------------------------
# History Service (DB VERSION)
# ---------------------------

from db.database import SessionLocal
from db.models.transaction import Transaction


class HistoryService:

    # ---------------------------
    # Get user history
    # ---------------------------
    @staticmethod
    def get_by_user(user_id):

        with SessionLocal() as db:
            return (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id)
                .order_by(Transaction.id.desc())
                .all()
            )

    # ---------------------------
    # Count (user)
    # ---------------------------
    @staticmethod
    def count(user_id):

        with SessionLocal() as db:
            return (
                db.query(Transaction)
                .filter(Transaction.user_id == user_id)
                .count()
            )

    # ---------------------------
    # Admin (all history)
    # ---------------------------
    @staticmethod
    def get_all(limit=1000):

        with SessionLocal() as db:
            return (
                db.query(Transaction)
                .order_by(Transaction.id.desc())
                .limit(limit)
                .all()
            )

    # ---------------------------
    # Count ALL (admin)
    # ---------------------------
    @staticmethod
    def count_all():

        with SessionLocal() as db:
            return db.query(Transaction).count()