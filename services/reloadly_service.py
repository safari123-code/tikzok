# ---------------------------
# Reloadly Service
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

# ---------------------------
# Token cache
# ---------------------------

_reloadly_token = None
_token_expiry = 0


# ---------------------------
# Get Reloadly token
# ---------------------------

def get_reloadly_token():

    global _reloadly_token, _token_expiry

    if _reloadly_token and time.time() < _token_expiry:
        return _reloadly_token

    client_id = os.getenv("RELOADLY_CLIENT_ID")
    client_secret = os.getenv("RELOADLY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Reloadly credentials missing")

    url = "https://auth.reloadly.com/oauth/token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "audience": RELOADLY_BASE_URL
    }

    res = requests.post(url, json=payload, timeout=10)
    res.raise_for_status()

    data = res.json()

    _reloadly_token = data.get("access_token")

    if not _reloadly_token:
        raise RuntimeError("Reloadly token missing")

    _token_expiry = time.time() + data.get("expires_in", 3600) - 60

    return _reloadly_token


# ---------------------------
# Phone operator lookup
# ---------------------------

def lookup_phone_number(phone: str, country: str):

    token = get_reloadly_token()

    url = f"{RELOADLY_BASE_URL}/operators/auto-detect/phone/{phone}/countries/{country}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:

        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return None

        data = res.json()

    except Exception:
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
# Reloadly Plans
# ---------------------------

def get_reloadly_plans(operator_id: int):

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    plans = []

    # ---------------------------
    # DATA PLANS
    # ---------------------------

    try:

        url = f"{RELOADLY_BASE_URL}/operators/{operator_id}/data-plans"

        res = requests.get(url, headers=headers, timeout=15)

        if res.status_code == 200:

            data = res.json()

            for p in data:

                plans.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "type": p.get("type") or "DATA",
                    "amount": p.get("amount"),
                    "currency": p.get("currencyCode"),
                })

    except Exception:
        pass


    # ---------------------------
    # BUNDLES
    # ---------------------------

    try:

        url = f"{RELOADLY_BASE_URL}/operators/{operator_id}/bundles"

        res = requests.get(url, headers=headers, timeout=15)

        if res.status_code == 200:

            data = res.json()

            for p in data:

                plans.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "type": p.get("type") or "COMBO",
                    "amount": p.get("amount"),
                    "currency": p.get("currencyCode"),
                })

    except Exception:
        pass


    return plans

# ---------------------------
# Get operators by country
# ---------------------------

def get_reloadly_operators_by_country(country_iso: str):

    token = get_reloadly_token()

    url = f"{RELOADLY_BASE_URL}/operators/countries/{country_iso.upper()}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:

        res = requests.get(url, headers=headers, timeout=15)

        if res.status_code != 200:
            return []

        data = res.json()

    except Exception:
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

# ---------------------------
# Send Topup
# ---------------------------

def send_topup(phone: str, amount: float):

    token = get_reloadly_token()

    # Detect operator automatically
    country = phone[:3].replace("+", "")[:2]

    lookup = lookup_phone_number(phone, country)

    if not lookup:
        raise RuntimeError("Operator detection failed")

    operator_id = lookup["operatorId"]
    country_code = lookup["countryCode"]

    url = f"{RELOADLY_BASE_URL}/topups"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    payload = {
        "operatorId": operator_id,
        "amount": float(amount),
        "useLocalAmount": False,
        "customIdentifier": f"tikzok-{phone}-{int(time.time())}",
        "recipientPhone": {
            "countryCode": country_code,
            "number": phone
        }
    }

    res = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20
    )

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly topup failed: {res.text}")

    return res.json()