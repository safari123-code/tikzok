# ---------------------------
# Feature: Reloadly Data Service (FINAL PRODUCTION HARDENED)
# ---------------------------

import uuid
from services.reloadly.auth_service import get_reloadly_token, _safe_request
from services.reloadly.operators_service import (
    lookup_phone_number,
    _extract_local_number,
    _normalize_phone,
    _normalize_country_iso
)
from config import RELOADLY_BASE_URL

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"


# ---------------------------
# Parse description (GB + durée)
# ---------------------------
def _parse_plan_description(desc: str):

    desc = (desc or "").lower()

    gb = ""
    validity = ""

    import re

    gb_match = re.search(r"(\d+)\s?gb", desc)
    if gb_match:
        gb = gb_match.group(1) + "GB"

    days_match = re.search(r"(\d+)\s?(day|days|jours)", desc)
    if days_match:
        validity = days_match.group(1) + " jours"

    return gb, validity


# ---------------------------
# Get Data Plans (SAFE PROD)
# ---------------------------
def get_reloadly_plans(operator_id: int):

    if not operator_id:
        return []

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        url = f"{RELOADLY_V1_URL}/operators/{operator_id}/data-plans"

        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("❌ Reloadly plans failed:", res.text)
            return []

        data = res.json()

        print("📡 DATA PLANS COUNT:", len(data) if data else 0)

        plans = []

        for p in data:

            description = p.get("description") or p.get("name") or ""

            gb, validity = _parse_plan_description(description)

            plans.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "amount": float(p.get("amount") or 0),
                "currency": p.get("currencyCode") or "EUR",
                "type": "DATA",
                "description": description,
                "gb": gb,
                "validity": validity
            })

        return plans

    except Exception as e:
        print("❌ Reloadly plans error:", e)
        return []


# ---------------------------
# Get Quote (RELOADLY API ONLY)
# ---------------------------
def get_reloadly_quote(operator_id: int, amount: float, phone: str = None, country_iso: str = None):

    if not operator_id or not amount:
        return None

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        # ---------------------------
        # 1. Operator details
        # ---------------------------
        url = f"{RELOADLY_BASE_URL}/operators/{operator_id}"
        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("❌ Operator fetch failed:", res.text)
            return None

        data = res.json()

        local_currency = (
            data.get("localCurrency")
            or (data.get("fx") or {}).get("currencyCode")
            or data.get("currencyCode")
            or (data.get("country") or {}).get("currencyCode")
        )

        if not local_currency:
            print("❌ Currency missing from Reloadly operator response")
            return None

        # ---------------------------
        # 2. Reloadly FX via suggestedAmountsMap
        # ---------------------------
        received_amount = None

        if phone and country_iso:
            try:
                safe_amount = max(1, round(amount))

                fx_url = (
                    f"{RELOADLY_BASE_URL}/operators/auto-detect/phone/{phone}"
                    f"/countries/{country_iso}"
                    f"?suggestedAmountsMap=true&suggestedAmounts={safe_amount}"
                )

                fx_res = _safe_request("GET", fx_url, headers=headers)

                if fx_res.status_code == 200:
                    fx_data = fx_res.json()
                    mapping = fx_data.get("suggestedAmountsMap") or {}

                    # on n'utilise QUE la donnée Reloadly
                    key = str(safe_amount)
                    received_amount = mapping.get(key)

                    # fallback Reloadly seulement:
                    # si la clé exacte n'existe pas mais qu'il y a d'autres clés
                    if received_amount is None and mapping:
                        try:
                            closest_key = min(
                                mapping.keys(),
                                key=lambda k: abs(float(k) - float(safe_amount))
                            )
                            received_amount = mapping.get(closest_key)
                        except Exception:
                            received_amount = None

            except Exception as e:
                print("❌ FX error:", e)

        # ---------------------------
        # 3. Return Reloadly-only value
        # ---------------------------
        return {
            "destinationAmount": float(received_amount) if received_amount is not None else None,
            "destinationCurrencyCode": local_currency
        }

    except Exception as e:
        print("❌ Reloadly quote error:", e)
        return None


# ---------------------------
# Send Data Topup (ASYNC SAFE)
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
    # Request
    # ---------------------------
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

    print("🚀 DATA TOPUP START:", custom_id)

    res = _safe_request("POST", url, headers=headers, json=payload, timeout=20)

    print("📡 DATA TOPUP STATUS:", res.status_code)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly DATA topup failed: {res.text}")

    data = res.json()

    return {
        "transaction_id": data.get("transactionId"),
        "custom_id": custom_id,
        "status": "PENDING"
    }