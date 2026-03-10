# ---------------------------
# services/history_service.py
# ---------------------------

from datetime import datetime
from flask import session


class HistoryService:
    """
    Session-based history storage.
    Future-ready for DB migration.
    """

    SESSION_KEY = "history_items"

    @classmethod
    def add(cls, phone: str, amount: str):
        """
        Add a recharge history entry.
        """

        history = session.get(cls.SESSION_KEY, [])

        history.insert(0, {
            "phone": phone,
            "amount": str(amount),
            "date": datetime.now().strftime("%d/%m/%Y • %H:%M"),
        })

        session[cls.SESSION_KEY] = history

    @classmethod
    def get_all(cls):
        """
        Get all history items.
        """
        return session.get(cls.SESSION_KEY, [])

    @classmethod
    def count(cls):
        """
        Get total history count.
        """
        return len(session.get(cls.SESSION_KEY, []))

    @classmethod
    def clear(cls):
        """
        Clear history (useful for testing).
        """
        session.pop(cls.SESSION_KEY, None)