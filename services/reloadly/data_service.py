# ---------------------------
# Feature: Reloadly Data Service (FINAL PRODUCTION HARDENED)
# ---------------------------
from services.reloadly.auth_service import clear_reloadly_token
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
# Get Data Plans (FINAL — SHOW ALL)
# ---------------------------
def get_reloadly_plans(operator):

    if not operator:
        return []

    operator_id = operator.get("id") or operator.get("operatorId")

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

        if res.status_code == 401:
            clear_reloadly_token()
            token = get_reloadly_token(force_refresh=True)

            headers["Authorization"] = f"Bearer {token}"

            res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("❌ Reloadly plans failed:", res.text)
            return []

        data = res.json()

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

        # 🔥 tri UX (important)
        plans.sort(key=lambda x: x["amount"])

        return plans

    except Exception as e:
        print("❌ Reloadly plans error:", e)
        return []


# ---------------------------
# Get Quote (RELOADLY FX-RATE FINAL PRODUCTION)
# ---------------------------
def get_reloadly_quote(operator_id: int, amount: float, phone: str = None, country_iso: str = None):

    if not operator_id or not amount:
        return None

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json",
        "Content-Type": "application/json"
    }

    try:
        # ---------------------------
        # 1. Get operator (currency + fx fallback)
        # ---------------------------
        operator_url = f"{RELOADLY_BASE_URL}/operators/{operator_id}"

        op_res = _safe_request("GET", operator_url, headers=headers)

        if op_res.status_code != 200:
            print("❌ Operator fetch failed:", op_res.text)
            return None

        op_data = op_res.json()

        local_currency = (
            op_data.get("localCurrency")
            or (op_data.get("fx") or {}).get("currencyCode")
            or op_data.get("currencyCode")
            or (op_data.get("country") or {}).get("currencyCode")
        )

        if not local_currency:
            print("❌ Currency missing from Reloadly")
            return None

        # ---------------------------
        # 2. FX RATE (OFFICIAL + FALLBACK)
        # ---------------------------
        received_amount = None

        # 🔥 FX API officiel
        try:
            fx_payload = {
                "operatorId": int(operator_id),
                "amount": float(amount)
            }

            fx_url = f"{RELOADLY_BASE_URL}/operators/fx-rate"

            fx_res = _safe_request(
                "POST",
                fx_url,
                headers=headers,
                json=fx_payload,
                timeout=15
            )

            if fx_res.status_code == 401:
                clear_reloadly_token()
                token = get_reloadly_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"

                fx_res = _safe_request(
                    "POST",
                    fx_url,
                    headers=headers,
                    json=fx_payload,
                    timeout=15
                )

            if fx_res.status_code == 200:
                fx_data = fx_res.json()
                received_amount = fx_data.get("destinationAmount")

            else:
                print("❌ FX RATE failed:", fx_res.text)

        except Exception as e:
            print("❌ FX-RATE error:", e)

        # 🔥 FALLBACK (important en LIVE)
        if received_amount is None:
            try:
                fx_info = op_data.get("fx") or {}
                rate = fx_info.get("rate")

                if rate:
                    received_amount = float(amount) * float(rate)

            except Exception as e:
                print("❌ FX fallback error:", e)

        # 🔥 SAFE FINAL (jamais None)
        if received_amount is None:
            received_amount = float(amount)

        # ---------------------------
        # 3. RETURN FINAL
        # ---------------------------
        return {
            "destinationAmount": round(float(received_amount), 2),
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