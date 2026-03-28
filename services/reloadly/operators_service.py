# ---------------------------
# Feature: Reloadly Operators Service (FINAL PRODUCTION)
# ---------------------------

from services.reloadly.auth_service import get_reloadly_token, _safe_request
from config import RELOADLY_BASE_URL

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"


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
# Lookup operator
# ---------------------------
def lookup_phone_number(phone: str, country: str):

    token = get_reloadly_token()

    normalized_phone = _extract_local_number(phone)
    normalized_country = _normalize_country_iso(country)

    if not normalized_phone or not normalized_country:
        return None

    url = f"https://topups.reloadly.com/operators/auto-detect/phone/{normalized_phone}/countries/{normalized_country}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

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
        "countryCode": (data.get("country") or {}).get("isoName"),
        "supportsData": data.get("data", False)
    }


# ---------------------------
# Get operators by country
# ---------------------------
def get_reloadly_operators_by_country(country_iso: str):

    token = get_reloadly_token()

    normalized_country = _normalize_country_iso(country_iso)
    if not normalized_country:
        return []

    url = f"{RELOADLY_BASE_URL}/operators/countries/{normalized_country}?includeBundles=true&includeData=true"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

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
            "logo_url": logo_url,
            "supports_data": op.get("supportsData"),
            "supports_bundles": op.get("supportsBundles"),
        })

    return operators


# ---------------------------
# Get operator amounts (FINAL MIGRATION)
# ---------------------------
def get_reloadly_operator_amounts(operator_id: int):

    if not operator_id:
        return {}

    token = get_reloadly_token()

    url = f"{RELOADLY_BASE_URL}/operators/{operator_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:
        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("❌ Operator details failed:", res.text)
            return {}

        data = res.json()

        fixed = data.get("fixedAmounts") or []

        min_amount = data.get("minAmount") or data.get("minLocalAmount")
        max_amount = data.get("maxAmount") or data.get("maxLocalAmount")

        # 🔥 fallback safe UX
        if not fixed and not min_amount:
            return {
                "fixedAmounts": [5, 10, 20, 50],
                "minAmount": 5,
                "maxAmount": 100,
                "localCurrency": data.get("localCurrency") or "EUR"
            }

        return {
            "denominationType": data.get("denominationType"),
            "fixedAmounts": fixed,
            "minAmount": min_amount,
            "maxAmount": max_amount,
            "localCurrency": data.get("localCurrency"),
        }

    except Exception as e:
        print("❌ Operator amounts error:", e)
        return {}