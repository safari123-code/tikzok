# ---------------------------
# Lookup Service (FINAL PRODUCTION)
# ---------------------------

import requests
import os

RELOADLY_BASE_URL = os.getenv("RELOADLY_BASE_URL", "https://topups.reloadly.com")
RELOADLY_TOKEN = os.getenv("RELOADLY_TOKEN")


# ---------------------------
# Helper: headers
# ---------------------------
def _headers():
    return {
        "Authorization": f"Bearer {RELOADLY_TOKEN}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }


# ---------------------------
# Auto detect operator
# ---------------------------
def get_reloadly_operator_auto_detect(phone: str, country_iso: str):
    """
    Detect operator using Reloadly API
    """

    if not phone or not country_iso:
        return None

    url = f"{RELOADLY_BASE_URL}/operators/auto-detect/phone/{phone}/countries/{country_iso}"

    try:
        res = requests.get(url, headers=_headers(), timeout=10)

        if res.status_code != 200:
            print(f"❌ Reloadly lookup failed: {res.text}")
            return None

        data = res.json()

        return _normalize_operator(data)

    except Exception as e:
        print(f"❌ Lookup exception: {e}")
        return None


# ---------------------------
# Normalize operator (IMPORTANT)
# ---------------------------
def _normalize_operator(data: dict):
    """
    Clean and normalize Reloadly operator response
    """

    if not data:
        return None

    return {
        "id": data.get("operatorId") or data.get("id"),
        "name": data.get("name"),
        "country": data.get("country", {}).get("isoName"),
        "logo_url": _extract_logo(data),
        "destinationCurrencyCode": data.get("destinationCurrencyCode"),
        "senderCurrencyCode": data.get("senderCurrencyCode"),
        "min_amount": data.get("minAmount"),
        "max_amount": data.get("maxAmount"),
    }


# ---------------------------
# Extract best logo
# ---------------------------
def _extract_logo(data: dict):
    logos = data.get("logoUrls") or []

    if not logos:
        return None

    # prends le logo medium si possible
    return logos[1] if len(logos) > 1 else logos[0]