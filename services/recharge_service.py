import os
import re
import time
import requests

# ---------------------------
# Phone normalization / validation
# ---------------------------
_PHONE_ALLOWED = re.compile(r"[^\d+]")


def normalize_phone_e164_light(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    s = _PHONE_ALLOWED.sub("", s)
    if not s.startswith("+"):
        s = "+" + s
    # keep '+' + digits only
    s = "+" + re.sub(r"[^\d]", "", s[1:])
    return s


def is_phone_length_valid(phone: str) -> bool:
    digits = re.sub(r"[^\d]", "", phone or "")
    # Flutter gating ~9 and max 15 digits (E.164 max 15)
    return 9 <= len(digits) <= 15


def detect_country_iso_from_phone(phone: str) -> str | None:
    # Minimal: support a few + use your Flutter default AF/FR behavior
    # (For full list, plug a countries dataset later)
    digits = re.sub(r"[^\d]", "", phone or "")
    if digits.startswith("93"):
        return "AF"
    if digits.startswith("33"):
        return "FR"
    if digits.startswith("49"):
        return "DE"
    if digits.startswith("39"):
        return "IT"
    if digits.startswith("34"):
        return "ES"
    if digits.startswith("1"):
        return "US"
    return None


# ---------------------------
# Reloadly (official) – wrappers
# ---------------------------
def _reloadly_headers() -> dict:
    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def get_reloadly_operator_auto_detect(phone: str, country_iso: str) -> dict:
    """
    Returns: {id, name, country_name, logo_url}
    Safe fallback if token missing or API fails.
    """
    phone = normalize_phone_e164_light(phone)
    if not phone or not country_iso:
        return {}

    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")
    if not token:
        return {}

    url = f"https://topups.reloadly.com/operators/auto-detect/phone/{phone}/countries/{country_iso}"
    try:
        res = requests.get(url, headers=_reloadly_headers(), timeout=10)
        if res.status_code != 200:
            return {}
        op = res.json()
        logo_urls = op.get("logoUrls") or []
        return {
            "id": op.get("id"),
            "name": op.get("name"),
            "country_name": (op.get("country") or {}).get("name"),
            "logo_url": logo_urls[0] if isinstance(logo_urls, list) and logo_urls else None,
            "country_iso": country_iso,
        }
    except Exception:
        return {}


def get_reloadly_operator_amounts(operator_id: int) -> dict:
    """
    Returns: {fixedAmounts: [..], minAmount: x, maxAmount: y}
    """
    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")
    if not token:
        return {}

    try:
        res = requests.get(
            f"https://topups.reloadly.com/operators/{operator_id}/amounts",
            headers=_reloadly_headers(),
            timeout=10,
        )
        if res.status_code != 200:
            return {}

        amt = res.json()
        fixed = amt.get("fixedAmounts") or []
        fixed_amounts = []
        for v in fixed:
            try:
                fixed_amounts.append(float(v))
            except Exception:
                pass

        return {
            "fixedAmounts": fixed_amounts,
            "minAmount": float(amt.get("minAmount")) if amt.get("minAmount") is not None else None,
            "maxAmount": float(amt.get("maxAmount")) if amt.get("maxAmount") is not None else None,
        }
    except Exception:
        return {}


# ---------------------------
# Quote (backend endpoint in Flutter)
# ---------------------------
def quote_local_amount(operator_id: int, amount: float) -> dict:
    """
    In Flutter you call TON_BACKEND_URL/api/reloadly/quote.
    Here we keep same concept locally.
    You can later implement true quote logic.
    """
    # Minimal placeholder: echoes EUR as local
    # Replace with real quote logic later.
    return {
        "localAmount": round(float(amount), 2),
        "localCurrency": "EUR",
        "ts": int(time.time()),
    }