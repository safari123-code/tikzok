# ---------------------------
# Feature: Reloadly Auth Service (FINAL PRODUCTION)
# ---------------------------

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from config import RELOADLY_AUTH_URL

load_dotenv()

logger = logging.getLogger(__name__)

_reloadly_token: Optional[str] = None
_token_expiry: float = 0.0


# ---------------------------
# Token cache helpers
# ---------------------------

def clear_reloadly_token() -> None:
    global _reloadly_token, _token_expiry
    _reloadly_token = None
    _token_expiry = 0.0


# ---------------------------
# Safe request (retry réseau + 5xx)
# ---------------------------

def _safe_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 15,
    retries: int = 2,
):
    last_error: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json,
                timeout=timeout,
            )

            # ✔ retourne direct si OK ou 4xx (logique métier)
            if response.status_code < 500:
                return response

            logger.warning(
                "Reloadly 5xx",
                extra={
                    "url": url,
                    "status": response.status_code,
                    "attempt": attempt + 1,
                },
            )

        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "Reloadly network error",
                extra={
                    "url": url,
                    "attempt": attempt + 1,
                    "error": str(exc),
                },
            )

        if attempt < retries:
            time.sleep(1.2 * (attempt + 1))

    if last_error:
        raise RuntimeError(f"Reloadly request failed: {last_error}")

    raise RuntimeError("Reloadly request failed")


# ---------------------------
# Get token (AUTO REFRESH)
# ---------------------------

def get_reloadly_token(force_refresh: bool = False) -> str:
    global _reloadly_token, _token_expiry

    now = time.time()

    # ✔ utilise cache si valide
    if not force_refresh and _reloadly_token and now < _token_expiry:
        return _reloadly_token

    client_id = os.getenv("RELOADLY_CLIENT_ID")
    client_secret = os.getenv("RELOADLY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Reloadly credentials missing")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "audience": "https://topups.reloadly.com",
    }

    response = _safe_request(
        "POST",
        RELOADLY_AUTH_URL,
        json=payload,
        timeout=15,
        retries=2,
    )

    if response.status_code != 200:
        try:
            data = response.json()
            message = data.get("message")
        except Exception:
            message = response.text or "Reloadly auth failed"

        logger.error("Reloadly auth failed", extra={"message": message})
        raise RuntimeError(message)

    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError("Invalid Reloadly auth response") from exc

    token = data.get("access_token")

    if not token:
        raise RuntimeError("Reloadly token missing")

    expires_in = int(data.get("expires_in", 3600))

    # ✔ marge sécurité
    expiry = time.time() + max(60, expires_in - 60)

    _reloadly_token = token
    _token_expiry = expiry

    logger.info("Reloadly token refreshed")

    return token