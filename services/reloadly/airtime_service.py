# ---------------------------
# Feature: Reloadly Airtime Service
# ---------------------------

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from config import RELOADLY_BASE_URL
from services.reloadly.auth_service import clear_reloadly_token, get_reloadly_token, _safe_request
from services.reloadly.operators_service import (
    lookup_phone_number,
    _extract_local_number,
    _normalize_phone,
    _normalize_country_iso,
)

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"


# ---------------------------
# Exceptions
# ---------------------------

class AirtimeServiceError(Exception):
    pass


class AirtimeValidationError(AirtimeServiceError):
    pass


class AirtimeProviderError(AirtimeServiceError):
    pass


# ---------------------------
# Helpers
# ---------------------------

def _build_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/com.reloadly.topups-v1+json",
    }


def _build_accept_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json",
    }


def _normalize_amount(amount: float | int | str) -> float:
    try:
        value = float(amount)
    except Exception as exc:
        raise AirtimeValidationError("Montant invalide") from exc

    if value <= 0:
        raise AirtimeValidationError("Le montant doit être supérieur à 0")

    return round(value, 2)


def _normalize_custom_identifier(custom_identifier: Optional[str]) -> str:
    value = str(custom_identifier or "").strip()
    if value:
        return value
    return f"tk_{uuid.uuid4().hex}"


def _extract_reloadly_error(response) -> str:
    try:
        data = response.json()
    except Exception:
        return response.text or "Erreur Reloadly inconnue"

    message = data.get("message")
    error_code = data.get("errorCode")

    if message and error_code:
        return f"{error_code}: {message}"

    return message or error_code or response.text or "Erreur Reloadly inconnue"


def _normalize_status(status: str | None) -> str:
    value = str(status or "").strip().upper()

    if value in {"SUCCESS", "SUCCESSFUL"}:
        return "SUCCESS"
    if value in {"PROCESSING", "PENDING"}:
        return "PROCESSING"
    if value == "REFUNDED":
        return "REFUNDED"
    if value == "FAILED":
        return "FAILED"

    return "UNKNOWN"


def _post_topup_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    token = get_reloadly_token()
    headers = _build_headers(token)
    response = _safe_request(
        "POST",
        f"{RELOADLY_BASE_URL}/topups",
        headers=headers,
        json=payload,
        timeout=20,
    )

    if response.status_code == 401:
        clear_reloadly_token()
        token = get_reloadly_token(force_refresh=True)
        headers = _build_headers(token)
        response = _safe_request(
            "POST",
            f"{RELOADLY_BASE_URL}/topups",
            headers=headers,
            json=payload,
            timeout=20,
        )

    if response.status_code not in (200, 201):
        raise AirtimeProviderError(_extract_reloadly_error(response))

    try:
        return response.json()
    except Exception as exc:
        raise AirtimeProviderError("Invalid Reloadly topup response") from exc


# ---------------------------
# Send Topup
# ---------------------------

def send_topup(
    phone: str,
    amount: float,
    country_iso: str | None = None,
    custom_identifier: str | None = None,
) -> Dict[str, Any]:
    normalized_phone = _normalize_phone(phone)
    normalized_country = _normalize_country_iso(country_iso)
    normalized_amount = _normalize_amount(amount)
    normalized_custom_identifier = _normalize_custom_identifier(custom_identifier)

    if not normalized_phone:
        raise AirtimeValidationError("Reloadly phone missing")

    if not normalized_country:
        raise AirtimeValidationError("Reloadly country ISO missing")

    lookup = lookup_phone_number(normalized_phone, normalized_country)

    if not lookup:
        raise AirtimeValidationError("Operator detection failed")

    operator_id = lookup.get("id")
    country_code = lookup.get("country_iso")

    if not operator_id or not country_code:
        raise AirtimeValidationError("Invalid operator data")

    payload = {
        "operatorId": int(operator_id),
        "amount": float(normalized_amount),
        "useLocalAmount": False,
        "customIdentifier": normalized_custom_identifier,
        "recipientPhone": {
            "countryCode": country_code,
            "number": _extract_local_number(normalized_phone),
        },
    }

    data = _post_topup_request(payload)

    return {
        "transaction_id": data.get("transactionId"),
        "custom_id": data.get("customIdentifier") or normalized_custom_identifier,
        "status": _normalize_status(data.get("status")),
        "operator_id": data.get("operatorId") or operator_id,
        "operator_name": data.get("operatorName"),
        "requested_amount": data.get("requestedAmount"),
        "requested_amount_currency_code": data.get("requestedAmountCurrencyCode"),
        "delivered_amount": data.get("deliveredAmount"),
        "delivered_amount_currency_code": data.get("deliveredAmountCurrencyCode"),
        "raw": data,
    }


# ---------------------------
# Get Topup Status
# ---------------------------

def get_topup_status(transaction_id: int | str | None) -> Dict[str, Any]:
    if transaction_id is None or str(transaction_id).strip() == "":
        raise AirtimeValidationError("transaction_id missing")

    token = get_reloadly_token()
    headers = _build_accept_headers(token)

    url = f"{RELOADLY_V1_URL}/topups/{int(transaction_id)}/status"
    response = _safe_request("GET", url, headers=headers, timeout=15)

    if response.status_code == 401:
        clear_reloadly_token()
        token = get_reloadly_token(force_refresh=True)
        headers = _build_accept_headers(token)
        response = _safe_request("GET", url, headers=headers, timeout=15)

    if response.status_code == 404:
        return {
            "status": "UNKNOWN",
            "transaction_id": int(transaction_id),
            "raw": {"message": "Transaction not found"},
        }

    if response.status_code != 200:
        raise AirtimeProviderError(_extract_reloadly_error(response))

    try:
        data = response.json()
    except Exception as exc:
        raise AirtimeProviderError("Invalid Reloadly status response") from exc

    transaction = data.get("transaction") or {}

    return {
        "status": _normalize_status(data.get("status")),
        "transaction_id": transaction.get("transactionId") or int(transaction_id),
        "custom_id": transaction.get("customIdentifier"),
        "operator_id": transaction.get("operatorId"),
        "operator_name": transaction.get("operatorName"),
        "requested_amount": transaction.get("requestedAmount"),
        "requested_amount_currency_code": transaction.get("requestedAmountCurrencyCode"),
        "delivered_amount": transaction.get("deliveredAmount"),
        "delivered_amount_currency_code": transaction.get("deliveredAmountCurrencyCode"),
        "country_code": transaction.get("countryCode"),
        "raw": data,
    }