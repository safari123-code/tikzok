# ---------------------------
# services/recharge_service.py
# ---------------------------

import os
import re
import time
import hashlib
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

    s = "+" + re.sub(r"[^\d]", "", s[1:])

    return s


def is_phone_length_valid(phone: str) -> bool:

    digits = re.sub(r"[^\d]", "", phone or "")

    return 9 <= len(digits) <= 15


# ---------------------------
# Country detection
# ---------------------------

def detect_country_iso_from_phone(phone: str) -> str | None:

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

    if digits.startswith("44"):
        return "GB"

    if digits.startswith("1"):
        return "US"

    return None


# ---------------------------
# Reloadly headers
# ---------------------------

def _reloadly_headers() -> dict:

    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json",
    }


# ---------------------------
# Reloadly auto operator detect
# ---------------------------

def get_reloadly_operator_auto_detect(phone: str, country_iso: str) -> dict:

    phone = normalize_phone_e164_light(phone)

    if not phone or not country_iso:
        return {}

    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")

    if not token:
        return {}

    url = f"https://topups.reloadly.com/operators/auto-detect/phone/{phone}/countries/{country_iso}"

    try:

        res = requests.get(
            url,
            headers=_reloadly_headers(),
            timeout=10
        )

        if res.status_code != 200:
            return {}

        op = res.json()

        logo_urls = op.get("logoUrls") or []

        logo = None
        if isinstance(logo_urls, list) and len(logo_urls) > 0:
            logo = logo_urls[0]

        return {
            "id": op.get("operatorId"),
            "name": op.get("name"),
            "country_name": (op.get("country") or {}).get("name"),
            "logo_url": logo,
            "country_iso": country_iso,
        }

    except Exception:
        return {}


# ---------------------------
# Reloadly operator amounts
# ---------------------------

def get_reloadly_operator_amounts(operator_id: int) -> dict:

    token = os.getenv("RELOADLY_ACCESS_TOKEN", "")

    if not token:
        return {}

    try:

        res = requests.get(
            f"https://topups.reloadly.com/operators/{operator_id}/amounts",
            headers=_reloadly_headers(),
            timeout=10
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
            "minAmount": float(amt.get("minAmount")) if amt.get("minAmount") else None,
            "maxAmount": float(amt.get("maxAmount")) if amt.get("maxAmount") else None,
        }

    except Exception:
        return {}


# ---------------------------
# Quote fallback
# ---------------------------

def quote_local_amount(operator_id: int, amount: float) -> dict:

    # fallback simple si Reloadly quote indisponible

    return {
        "localAmount": round(float(amount) * 70),  # estimation AFN
        "localCurrency": "AFN",
        "ts": int(time.time()),
    }


# ---------------------------
# Idempotency key
# ---------------------------

def generate_idempotency(user_id, phone, amount):

    raw = f"{user_id}:{phone}:{amount}:{int(time.time() // 60)}"

    return hashlib.sha256(raw.encode()).hexdigest()