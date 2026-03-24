# ---------------------------
# services/recharge_service.py (FINAL PRO SAFE)
# ---------------------------

import re
import time
import hashlib


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
# Quote fallback (SAFE ONLY)
# ---------------------------

def quote_local_amount(operator_id: int, amount: float) -> dict:
    """
    ⚠️ Fallback uniquement si Reloadly indisponible
    Ne doit PAS être utilisé en priorité
    """

    return {
        "localAmount": float(amount),  # ⚠️ neutre → pas de faux taux
        "localCurrency": "EUR",        # ⚠️ éviter mensonge FX
        "ts": int(time.time()),
    }


# ---------------------------
# Idempotency key (PRO SAFE)
# ---------------------------

def generate_idempotency(user_id, phone, amount):

    raw = f"{user_id}:{phone}:{amount}:{int(time.time() // 60)}"

    return hashlib.sha256(raw.encode()).hexdigest()