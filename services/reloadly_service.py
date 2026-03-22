# ---------------------------
# Reloadly Service (Production Ready)
# ---------------------------

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Config
# ---------------------------
RELOADLY_BASE_URL = os.getenv(
    "RELOADLY_BASE_URL",
    "https://topups.reloadly.com"
)

RELOADLY_AUTH_URL = os.getenv(
    "RELOADLY_AUTH_URL",
    "https://auth.reloadly.com/oauth/token"
)

# ---------------------------
# Token cache
# ---------------------------
_reloadly_token = None
_token_expiry = 0


# ---------------------------
# Helpers
# ---------------------------
def _normalize_phone(phone: str) -> str:
    return "".join(ch for ch in str(phone or "") if ch.isdigit() or ch == "+")


def _normalize_country_iso(country_iso: str | None) -> str:
    return str(country_iso or "").strip().upper()


def _extract_local_number(phone: str) -> str:
    normalized = _normalize_phone(phone)
    return normalized[1:] if normalized.startswith("+") else normalized


# ---------------------------
# Safe request (retry)
# ---------------------------
def _safe_request(method, url, headers=None, json=None, timeout=15, retries=2):

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


# ---------------------------
# Get token
# ---------------------------
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
        "audience": RELOADLY_BASE_URL
    }

    res = _safe_request("POST", RELOADLY_AUTH_URL, json=payload)

    data = res.json()

    _reloadly_token = data.get("access_token")

    if not _reloadly_token:
        raise RuntimeError("Reloadly token missing")

    _token_expiry = time.time() + data.get("expires_in", 3600) - 60

    return _reloadly_token


# ---------------------------
# Lookup operator
# ---------------------------
def lookup_phone_number(phone: str, country: str):

    token = get_reloadly_token()

    normalized_phone = _extract_local_number(phone)
    normalized_country = _normalize_country_iso(country)

    if not normalized_phone or not normalized_country:
        return None

    url = f"{RELOADLY_BASE_URL}/operators/auto-detect/phone/{normalized_phone}/countries/{normalized_country}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("Reloadly lookup failed:", res.text)
            return None

        data = res.json()

    except Exception as e:
        print("Reloadly lookup exception:", e)
        return None

    logos = data.get("logoUrls") or []

    logo_url = None
    if logos:
        logo_url = logos[0]["url"] if isinstance(logos[0], dict) else logos[0]

    return {
        "operatorId": data.get("operatorId"),
        "name": data.get("name"),
        "logoUrl": logo_url,
        "countryName": (data.get("country") or {}).get("name"),
        "countryCode": (data.get("country") or {}).get("isoName")
    }


# ---------------------------
# Send Topup (FINAL)
# ---------------------------
def send_topup(phone: str, amount: float, country_iso: str | None = None):

    token = get_reloadly_token()

    normalized_phone = _normalize_phone(phone)
    normalized_country = _normalize_country_iso(country_iso)

    if not normalized_phone:
        raise RuntimeError("Reloadly phone missing")

    if not normalized_country:
        raise RuntimeError("Reloadly country ISO missing")

    # ---------------------------
    # Operator detection
    # ---------------------------
    lookup = lookup_phone_number(normalized_phone, normalized_country)

    if not lookup:
        raise RuntimeError("Operator detection failed")

    operator_id = lookup["operatorId"]
    country_code = lookup["countryCode"]

    if not operator_id or not country_code:
        raise RuntimeError("Invalid operator data")

    # ---------------------------
    # Idempotency (CRITICAL)
    # ---------------------------
    unique_id = f"tikzok-{normalized_phone}-{int(time.time())}"

    url = f"{RELOADLY_BASE_URL}/topups"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    payload = {
        "operatorId": int(operator_id),
        "amount": float(amount),
        "useLocalAmount": False,
        "customIdentifier": unique_id,
        "recipientPhone": {
            "countryCode": country_code,
            "number": _extract_local_number(normalized_phone)
        }
    }

    print("🚀 Reloadly topup:", payload)

    res = _safe_request("POST", url, headers=headers, json=payload, timeout=20)

    print("📡 Reloadly response:", res.status_code, res.text)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly topup failed: {res.text}")

    return res.json()

def get_reloadly_operators_by_country(country_iso: str):

    token = get_reloadly_token()

    normalized_country = _normalize_country_iso(country_iso)
    if not normalized_country:
        return []

    url = f"{RELOADLY_BASE_URL}/operators/countries/{normalized_country}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("Reloadly operators failed:", res.text)
            return []

        data = res.json()

    except Exception as e:
        print("Reloadly operators error:", e)
        return []

    operators = []

    for op in data:
        logos = op.get("logoUrls") or []

        logo_url = None
        if logos:
            logo_url = logos[0]["url"] if isinstance(logos[0], dict) else logos[0]

        operators.append({
            "id": op.get("operatorId"),
            "name": op.get("name"),
            "country": (op.get("country") or {}).get("name"),
            "country_iso": (op.get("country") or {}).get("isoName"),
            "logo_url": logo_url
        })

    return operators

def get_reloadly_plans(operator_id: int):

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    plans = []

    try:
        url = f"{RELOADLY_BASE_URL}/operators/{operator_id}/data-plans"

        res = _safe_request("GET", url, headers=headers)

        if res.status_code == 200:
            for p in res.json():
                plans.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "amount": p.get("amount"),
                    "currency": p.get("currencyCode"),
                    "type": "DATA"
                })

    except Exception as e:
        print("Reloadly plans error:", e)

    return plans