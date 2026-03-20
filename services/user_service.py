# ---------------------------
# User Service (FINAL PRO)
# ---------------------------

import json
import os
import uuid
from datetime import datetime

USERS_FILE = "data/users.json"


class UserService:

    # ---------------------------
    # Load users
    # ---------------------------
    @staticmethod
    def _load():
        if not os.path.exists(USERS_FILE):
            return []

        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    # ---------------------------
    # Save users
    # ---------------------------
    @staticmethod
    def _save(data):
        os.makedirs("data", exist_ok=True)

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---------------------------
    # Find or create user
    # ---------------------------
    @classmethod
    def find_or_create(cls, email=None, phone=None, name=None):

        users = cls._load()

        for u in users:
            if email and u.get("email") == email:
                return u

            if phone and u.get("phone") == phone:
                return u

        user = {
            "user_id": uuid.uuid4().hex,
            "email": email,
            "phone": phone,
            "name": name or "Utilisateur",
            "avatar": None,
            "created_at": datetime.utcnow().isoformat()
        }

        users.append(user)
        cls._save(users)

        return user

    # ---------------------------
    # Get user by id
    # ---------------------------
    @classmethod
    def get_by_id(cls, user_id):

        if not user_id:
            return None

        users = cls._load()

        for u in users:
            if u.get("user_id") == user_id:
                return u

        return None

    # ---------------------------
    # Update profile
    # ---------------------------
    @classmethod
    def update(cls, user_id, name=None):

        users = cls._load()

        for u in users:
            if u["user_id"] == user_id:
                if name:
                    u["name"] = name

        cls._save(users)

    # ---------------------------
    # Update avatar
    # ---------------------------
    @classmethod
    def update_avatar(cls, user_id, avatar_url):

        users = cls._load()

        for u in users:
            if u["user_id"] == user_id:
                u["avatar"] = avatar_url

        cls._save(users)