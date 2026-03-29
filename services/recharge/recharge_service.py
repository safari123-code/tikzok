# ---------------------------
# Feature: Recharge Service
# ---------------------------

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, ROUND_HALF_UP


# ---------------------------
# Phone normalization / validation
# ---------------------------

_PHONE_ALLOWED = re.compile(r"[^\d+]")


def normalize_phone_e164_light(raw: str) -> str:
    if raw is None:
        return ""

    value = str(raw).strip()

    if not value:
        return ""

    value = _PHONE_ALLOWED.sub("", value)

    if not value.startswith("+"):
        value = "+" + value

    value = "+" + re.sub(r"[^\d]", "", value[1:])

    return value


def is_phone_length_valid(phone: str) -> bool:
    digits = re.sub(r"[^\d]", "", phone or "")
    return 9 <= len(digits) <= 15


# ---------------------------
# Country detection
# ---------------------------

_COUNTRY_PREFIXES = [
    ("+225", "CI"),
    ("+212", "MA"),
    ("+234", "NG"),
    ("+237", "CM"),
    ("+90", "TR"),
    ("+93", "AF"),
    ("+49", "DE"),
    ("+44", "GB"),
    ("+39", "IT"),
    ("+34", "ES"),
    ("+33", "FR"),
    ("+1", "US"),
]


def detect_country_iso_from_phone(phone: str) -> str | None:
    normalized = normalize_phone_e164_light(phone)

    for prefix, iso in _COUNTRY_PREFIXES:
        if normalized.startswith(prefix):
            return iso

    return None


# ---------------------------
# Quote fallback
# ---------------------------

def quote_local_amount(operator_id: int, amount: float) -> dict:
    try:
        value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        value = Decimal("0.00")

    return {
        "destinationAmount": float(value),
        "destinationCurrencyCode": "EUR",
        "localAmount": float(value),
        "localCurrency": "EUR",
        "isFallback": True,
    }


# ---------------------------
# Idempotency key
# ---------------------------

def generate_idempotency(payment_reference, phone, amount=None, plan_id=None):
    raw = f"{payment_reference}:{phone}:{amount or ''}:{plan_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()