# ---------------------------
# Idempotency Service (PRO SAFE)
# ---------------------------

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional


class IdempotencyService:
    """
    Service d'idempotence robuste :
    - évite double paiement
    - évite double recharge
    - thread-safe
    - prêt pour Redis / DB
    """

    _store: Dict[str, Dict[str, Any]] = {}
    _locks: Dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    # TTL (optionnel, sécurité mémoire)
    _ttl_seconds = 3600 * 6  # 6h

    # ---------------------------
    # Internal lock per key
    # ---------------------------
    @classmethod
    def _get_lock(cls, key: str) -> threading.Lock:
        with cls._global_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]

    # ---------------------------
    # Cleanup (auto mémoire)
    # ---------------------------
    @classmethod
    def _cleanup(cls):
        now = int(time.time())

        keys_to_delete = []

        for key, value in cls._store.items():
            created_at = value.get("created_at", now)
            if now - created_at > cls._ttl_seconds:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            cls._store.pop(key, None)
            cls._locks.pop(key, None)

    # ---------------------------
    # Get result
    # ---------------------------
    @classmethod
    def get_result(cls, key: str) -> Optional[Dict[str, Any]]:
        if not key:
            return None

        cls._cleanup()

        item = cls._store.get(key)
        if not item:
            return None

        # copie safe
        return dict(item)

    # ---------------------------
    # Store result (SUCCESS / FAILED)
    # ---------------------------
    @classmethod
    def store_result(cls, key: str, payload: Dict[str, Any]):
        if not key:
            return

        lock = cls._get_lock(key)

        with lock:
            existing = cls._store.get(key)

            # 🔒 ne jamais écraser un SUCCESS
            if existing and existing.get("status") == "SUCCESS":
                return

            cls._store[key] = {
                **payload,
                "created_at": existing.get("created_at") if existing else int(time.time()),
                "updated_at": int(time.time()),
            }

    # ---------------------------
    # Mark processing (NEW)
    # ---------------------------
    @classmethod
    def mark_processing(cls, key: str):
        if not key:
            return

        lock = cls._get_lock(key)

        with lock:
            cls._store[key] = {
                "status": "PROCESSING",
                "created_at": int(time.time()),
                "updated_at": int(time.time()),
            }

    # ---------------------------
    # Check if already processed
    # ---------------------------
    @classmethod
    def is_processed(cls, key: str) -> bool:
        item = cls._store.get(key)
        if not item:
            return False

        return item.get("status") == "SUCCESS"

    # ---------------------------
    # Safe execute wrapper (OPTIONAL)
    # ---------------------------
    @classmethod
    def execute_once(cls, key: str, fn):
        """
        Exécute une fonction une seule fois.
        Si déjà exécuté → retourne résultat existant.
        """

        if not key:
            return fn()

        lock = cls._get_lock(key)

        with lock:

            existing = cls._store.get(key)

            if existing:
                return existing

            try:
                cls.mark_processing(key)

                result = fn()

                cls.store_result(
                    key,
                    {
                        "status": "SUCCESS",
                        "result": result,
                    },
                )

                return result

            except Exception as e:
                cls.store_result(
                    key,
                    {
                        "status": "FAILED",
                        "error": str(e),
                    },
                )
                raise