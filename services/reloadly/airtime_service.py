import uuid
from services.reloadly.auth_service import get_reloadly_token, _safe_request
from services.reloadly.operators_service import lookup_phone_number, _extract_local_number, _normalize_phone, _normalize_country_iso
from config import RELOADLY_BASE_URL

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"


# ---------------------------
# Send Topup (FINAL PRO - OFFICIAL ENDPOINT)
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

    # 🔥 idempotency clé
    custom_id = f"tk_{uuid.uuid4().hex}"

    url = f"{RELOADLY_BASE_URL}/topups"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    payload = {
        "operatorId": int(operator_id),

        # 🔥 IMPORTANT
        "amount": float(amount),

        # 🔥 CRITICAL (production)
        "useLocalAmount": True,

        "customIdentifier": custom_id,

        "recipientPhone": {
            "countryCode": country_code,
            # ⚠️ SANS "+"
            "number": _extract_local_number(normalized_phone)
        }
    }

    print("🚀 TOPUP PAYLOAD:", payload)

    res = _safe_request("POST", url, headers=headers, json=payload, timeout=20)

    print("📡 Reloadly response:", res.status_code, res.text)

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly topup failed: {res.text}")

    data = res.json()

    return {
        "transaction_id": data.get("transactionId"),
        "custom_id": custom_id,
        "status": "PENDING"
    }


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
            return {"status": "PROCESSING"}

        data = res.json()

    except Exception:
        return {"status": "PROCESSING"}

    return {
        "status": data.get("status", "PROCESSING"),
        "raw": data
    }