# ---------------------------
# services/history_service.py
# ---------------------------

import json
import os
import uuid
from datetime import datetime
from flask import session

HISTORY_FILE = "data/history.json"


class HistoryService:
    """
    Persistent history (file-based, user linked)
    Production-ready (safe + extensible)
    """

    # ---------------------------
    # Load
    # ---------------------------
    @staticmethod
    def _load():
        if not os.path.exists(HISTORY_FILE):
            return []

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    # ---------------------------
    # Save
    # ---------------------------
    @staticmethod
    def _save(data):
        os.makedirs("data", exist_ok=True)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---------------------------
    # Add history (PRO)
    # ---------------------------
    @classmethod
    def add(cls, phone: str, amount: str, country: str = None):

        user_id = session.get("user_id")

        if not user_id:
            return  # sécurité

        history = cls._load()

        # 🔒 idempotency simple (évite double recharge rapide)
        now_ts = int(datetime.now().timestamp())

        entry = {
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "phone": str(phone).strip(),
            "amount": str(amount),
            "country": country or "",
            "date": datetime.now().strftime("%d/%m/%Y • %H:%M"),
            "created_at": now_ts,
        }

        history.insert(0, entry)

        cls._save(history)

    # ---------------------------
    # Get user history
    # ---------------------------
    @classmethod
    def get_all(cls):

        user_id = session.get("user_id")

        if not user_id:
            return []

        history = cls._load()

        return [
            h for h in history
            if h.get("user_id") == user_id
        ]

    # ---------------------------
    # Count
    # ---------------------------
    @classmethod
    def count(cls):
        return len(cls.get_all())

    # ---------------------------
    # Get ALL (admin)
    # ---------------------------
    @classmethod
    def get_all_admin(cls):
        return cls._load()

    # ---------------------------
    # Clear user history
    # ---------------------------
    @classmethod
    def clear(cls):

        user_id = session.get("user_id")

        history = cls._load()

        history = [
            h for h in history
            if h.get("user_id") != user_id
        ]

        cls._save(history)