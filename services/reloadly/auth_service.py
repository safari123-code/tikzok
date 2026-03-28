import os
import time
import requests
from dotenv import load_dotenv
from config import RELOADLY_BASE_URL, RELOADLY_AUTH_URL

load_dotenv()

_reloadly_token = None
_token_expiry = 0


def _safe_request(method, url, headers=None, json=None, timeout=15, retries=2):
    import time

    for attempt in range(retries + 1):
        try:
            res = requests.request(
                method,
                url,
                headers=headers,
                json=json,
                timeout=timeout
            )

            if res.status_code < 500:
                return res

        except Exception as e:
            print("Reloadly request error:", e)

        time.sleep(1.2 * (attempt + 1))

    raise RuntimeError("Reloadly request failed after retries")


def get_reloadly_token():
    global _reloadly_token, _token_expiry

    if _reloadly_token and time.time() < _token_expiry:
        return _reloadly_token

    client_id = os.getenv("RELOADLY_CLIENT_ID")
    client_secret = os.getenv("RELOADLY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Reloadly credentials missing")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "audience":  "https://topups.reloadly.com"  # ✅ FIX CRITIQUE
    }

    res = _safe_request("POST", RELOADLY_AUTH_URL, json=payload)

    data = res.json()

    token = data.get("access_token")

    if not token:
        raise RuntimeError("Reloadly token missing")

    _reloadly_token = token
    _token_expiry = time.time() + data.get("expires_in", 3600) - 60

    return _reloadly_token