# ---------------------------
# Reloadly Service (Production Ready)
# ---------------------------

import os
import time
import uuid
import requests
from dotenv import load_dotenv
from config import RELOADLY_BASE_URL, RELOADLY_AUTH_URL

load_dotenv()

# ---------------------------
# Config (FINAL CLEAN)
# ---------------------------

# 🔥 Base URL vient du config.py (ne pas écraser)
# 🔥 On dérive uniquement le V1

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"
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

    url = (
    f"https://topups.reloadly.com/operators/auto-detect/"
    f"phone/{normalized_phone}/countries/{normalized_country}"
 )

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
        "countryCode": (data.get("country") or {}).get("isoName"),
        "supportsData": data.get("data", False)
    }


# ---------------------------
# Send Topup (ASYNC + SAFE)
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
    # Idempotency (PRO)
    # ---------------------------
    unique_id = f"tk_{uuid.uuid4().hex}"

    url = f"{RELOADLY_V1_URL}/topups-async"

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

    print("🚀 Reloadly topup started:", unique_id)

    res = _safe_request("POST", url, headers=headers, json=payload, timeout=20)

    print("📡 Reloadly response:", res.status_code)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly topup failed: {res.text}")

    data = res.json()

    return {
        "transaction_id": data.get("transactionId"),
        "custom_id": unique_id,
        "status": "PENDING"
    }


# ---------------------------
# Get Operators by Country (DATA + BUNDLES)
# ---------------------------
def get_reloadly_operators_by_country(country_iso: str):

    token = get_reloadly_token()

    normalized_country = _normalize_country_iso(country_iso)
    if not normalized_country:
        return []

    # 🔥 ENDPOINT PROPRE
    url = f"{RELOADLY_V1_URL}/operators/countries/{normalized_country}?includeBundles=true&includeData=true"

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
            "logo_url": logo_url,
            "supports_data": op.get("supportsData"),
            "supports_bundles": op.get("supportsBundles"),
        })

    return operators


# ---------------------------
# Get Topup Status (ASYNC FIX)
# ---------------------------
def get_topup_status(transaction_id: int):

    token = get_reloadly_token()

    url = f"{RELOADLY_V1_URL}/topups/{transaction_id}/status"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

        if res.status_code == 404:
            return {"status": "PROCESSING"}

        if res.status_code != 200:
            print("Reloadly status failed:", res.text)
            return {"status": "PROCESSING"}

        data = res.json()

    except Exception as e:
        print("Reloadly status error:", e)
        return {"status": "PROCESSING"}

    return {
        "status": data.get("status", "PROCESSING"),
        "raw": data
    }


# ---------------------------
# Get Reloadly Plans (Data)
# ---------------------------
def get_reloadly_plans(operator_id: int):

    if not operator_id:
        return []

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    plans = []

    try:
        url = f"{RELOADLY_V1_URL}/operators/{operator_id}/data-plans"

        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("Reloadly plans failed:", res.text)
            return []

        data = res.json()

        for p in data:
            plans.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "amount": p.get("amount"),
                "currency": p.get("currencyCode"),
                "type": "DATA",
                "description": p.get("description") or p.get("name")
            })

    except Exception as e:
        print("Reloadly plans error:", e)

    return plans


# ---------------------------
# Get Reloadly Quote (FINAL FIXED)
# ---------------------------
def get_reloadly_quote(operator_id: int, amount: float):

    token = get_reloadly_token()

    # ✅ IMPORTANT : PAS de /v1 ici
    url = f"{RELOADLY_BASE_URL}/topups/quote"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    payload = {
        "operatorId": int(operator_id),
        "amount": float(amount),
        "useLocalAmount": False
    }

    try:
        res = _safe_request("POST", url, headers=headers, json=payload)

        print("📡 QUOTE STATUS:", res.status_code)
        print("📡 QUOTE RESPONSE:", res.text)

        if res.status_code != 200:
            return None

        data = res.json()

        if not data.get("localAmount") or not data.get("localCurrency"):
            print("⚠️ Invalid quote data")
            return None

        return data

    except Exception as e:
        print("❌ Reloadly quote error:", e)
        return None

# ---------------------------
# Send Data Topup (FINAL)
# ---------------------------
def send_data_topup(phone: str, plan_id: int, country_iso: str):

    token = get_reloadly_token()

    normalized_phone = _normalize_phone(phone)
    normalized_country = _normalize_country_iso(country_iso)

    if not normalized_phone:
        raise RuntimeError("Reloadly phone missing")

    if not normalized_country:
        raise RuntimeError("Reloadly country ISO missing")

    if not plan_id:
        raise RuntimeError("Invalid plan id")

    lookup = lookup_phone_number(normalized_phone, normalized_country)

    if not lookup:
        raise RuntimeError("Operator detection failed")

    operator_id = lookup["operatorId"]
    country_code = lookup["countryCode"]

    if not operator_id or not country_code:
        raise RuntimeError("Invalid operator data")

    url = f"{RELOADLY_V1_URL}/topups-async"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    custom_id = f"tk_data_{uuid.uuid4().hex}"

    payload = {
        "operatorId": int(operator_id),
        "planId": int(plan_id),
        "customIdentifier": custom_id,
        "recipientPhone": {
            "countryCode": country_code,
            "number": _extract_local_number(normalized_phone)
        }
    }

    print("🚀 Reloadly DATA topup:", custom_id)

    res = _safe_request("POST", url, headers=headers, json=payload, timeout=20)

    print("📡 Reloadly DATA response:", res.status_code)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly DATA topup failed: {res.text}")

    data = res.json()

    return {
        "transaction_id": data.get("transactionId"),
        "custom_id": custom_id,
        "status": "PENDING"
    }
