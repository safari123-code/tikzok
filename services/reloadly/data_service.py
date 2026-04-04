# ---------------------------
# Feature: Reloadly Data Service
# ---------------------------

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from config import RELOADLY_BASE_URL
from services.reloadly.auth_service import clear_reloadly_token, get_reloadly_token, _safe_request
from services.reloadly.operators_service import (
    lookup_phone_number,
    _extract_local_number,
    _normalize_country_iso,
    _normalize_phone,
)

logger = logging.getLogger(__name__)

RELOADLY_V1_URL = f"{RELOADLY_BASE_URL}/v1"


# ---------------------------
# Helpers
# ---------------------------

def _build_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json",
        "Content-Type": "application/json",
    }


def _safe_json(response) -> Any:
    try:
        return response.json()
    except Exception:
        return None


def _extract_error_message(response) -> str:
    data = _safe_json(response)

    if isinstance(data, dict):
        message = data.get("message")
        error_code = data.get("errorCode")
        if message and error_code:
            return f"{error_code}: {message}"
        return message or error_code or response.text or "Reloadly error"

    return response.text or "Reloadly error"


def _normalize_status(status: str | None) -> str:
    value = str(status or "").strip().upper()

    if value in {"SUCCESS", "SUCCESSFUL"}:
        return "SUCCESS"
    if value in {"PROCESSING", "PENDING"}:
        return "PROCESSING"
    if value == "FAILED":
        return "FAILED"
    if value == "REFUNDED":
        return "REFUNDED"

    return "UNKNOWN"


def _lookup_operator(phone: str, country_iso: str) -> Dict[str, Any]:
    lookup = lookup_phone_number(phone, country_iso)

    if not lookup:
        raise RuntimeError("Operator detection failed")

    operator_id = (
        lookup.get("id")
        or lookup.get("operatorId")
    )

    country_code = (
        lookup.get("country_iso")
        or lookup.get("countryCode")
        or lookup.get("country_code")
    )

    if not operator_id or not country_code:
        raise RuntimeError("Invalid operator data")

    return {
        "operator_id": int(operator_id),
        "country_code": str(country_code).upper(),
        "raw": lookup,
    }


def _request_with_token_refresh(
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 15,
):
    response = _safe_request(
        method,
        url,
        headers=headers,
        json=json,
        timeout=timeout,
    )

    if response.status_code == 401:
        clear_reloadly_token()
        token = get_reloadly_token(force_refresh=True)
        headers = dict(headers)
        headers["Authorization"] = f"Bearer {token}"

        response = _safe_request(
            method,
            url,
            headers=headers,
            json=json,
            timeout=timeout,
        )

    return response


# ---------------------------
# Parse description
# ---------------------------

def _parse_plan_description(desc: str) -> Tuple[str, str]:
    import re

    value = str(desc or "").lower()

    gb = ""
    validity = ""

    gb_match = re.search(r"(\d+(?:[.,]\d+)?)\s?gb", value)
    if gb_match:
        gb = gb_match.group(1).replace(",", ".") + "GB"

    days_match = re.search(r"(\d+)\s?(day|days|jour|jours)", value)
    if days_match:
        validity = days_match.group(1) + " jours"

    return gb, validity


# ---------------------------
# Get Data Plans (FINAL WORKING)
# ---------------------------

def get_reloadly_plans(operator: Dict[str, Any] | None) -> List[Dict[str, Any]]:

    if not operator:
        return []

    # ---------------------------
    # Operator ID
    # ---------------------------
    operator_id = (
        operator.get("id")
        or operator.get("operatorId")
        or operator.get("operator_id")
    )

    logger.info("OPERATOR ID USED: %s", operator_id)

    if not operator_id:
        return []

    token = get_reloadly_token()
    headers = _build_headers(token)

    # ---------------------------
    # 🔥 VRAIS endpoints
    # ---------------------------
    urls = [
        f"{RELOADLY_V1_URL}/operators/{int(operator_id)}/data-plans",
        f"{RELOADLY_BASE_URL}/operators/{int(operator_id)}/bundles",
    ]

    data: List[Dict[str, Any]] = []

    for url in urls:
        try:
            res = _request_with_token_refresh(
                "GET",
                url,
                headers=headers,
                timeout=20,
            )

            logger.info("FETCH URL: %s STATUS: %s", url, res.status_code)

            if res.status_code != 200:
                continue

            payload = _safe_json(res)

            logger.info("RAW RESPONSE: %s", payload)

            # ---------------------------
            # FIX STRUCTURE
            # ---------------------------
            if isinstance(payload, dict):
                payload = payload.get("content") or payload.get("data") or []

            if isinstance(payload, list) and payload:
                data = payload
                break

        except Exception as exc:
            logger.exception("Reloadly plans exception: %s", exc)

    if not data:
        logger.warning("⚠️ No plans → fallback airtime")
        return []

    # ---------------------------
    # Build plans
    # ---------------------------
    plans: List[Dict[str, Any]] = []

    for plan in data:
        try:
            amount = float(plan.get("amount") or 0)
        except Exception:
            continue

        if amount <= 0:
            continue

        plan_id = (
            plan.get("productId")  # bundles
            or plan.get("id")
        )

        if not plan_id:
            continue

        description = plan.get("description") or plan.get("name") or ""

        gb, validity = _parse_plan_description(description)

        if gb and validity:
            display_name = f"{gb} • {validity}"
        elif gb:
            display_name = gb
        elif validity:
            display_name = validity
        else:
            display_name = description

        plans.append({
            "id": int(plan_id),
            "name": plan.get("name") or description,
            "amount": round(amount, 2),
            "currency": plan.get("currencyCode") or "EUR",
            "type": "DATA",
            "description": description,
            "gb": gb,
            "validity": validity,
            "display_name": display_name,
        })

    plans.sort(key=lambda item: item["amount"])

    logger.info("Reloadly plans parsed", extra={"count": len(plans)})

    return plans


# ---------------------------
# Get Quote
# ---------------------------

def get_reloadly_quote(
    operator_id: int,
    amount: float,
    phone: str | None = None,
    country_iso: str | None = None,
) -> Optional[Dict[str, Any]]:
    if not operator_id:
        return None

    try:
        normalized_amount = round(float(amount), 2)
    except Exception:
        return None

    if normalized_amount <= 0:
        return None

    token = get_reloadly_token()
    headers = _build_headers(token)

    try:
        operator_url = f"{RELOADLY_BASE_URL}/operators/{int(operator_id)}"
        op_res = _request_with_token_refresh(
            "GET",
            operator_url,
            headers=headers,
            timeout=15,
        )

        if op_res.status_code != 200:
            logger.warning("Reloadly operator fetch failed: %s", op_res.text)
            return None

        op_data = _safe_json(op_res) or {}

        local_currency = (
            op_data.get("destinationCurrencyCode")
            or op_data.get("localCurrency")
            or (op_data.get("fx") or {}).get("currencyCode")
            or op_data.get("currencyCode")
            or ((op_data.get("country") or {}).get("currencyCode"))
        )

        if not local_currency:
            return None

        destination_amount: Optional[float] = None

        fx_payload = {
            "operatorId": int(operator_id),
            "amount": normalized_amount,
        }

        fx_url = f"{RELOADLY_BASE_URL}/operators/fx-rate"
        fx_res = _request_with_token_refresh(
            "POST",
            fx_url,
            headers=headers,
            json=fx_payload,
            timeout=15,
        )

        if fx_res.status_code == 200:
            fx_data = _safe_json(fx_res) or {}
            try:
                raw_destination_amount = fx_data.get("destinationAmount")
                if raw_destination_amount is not None:
                    destination_amount = float(raw_destination_amount)
            except Exception:
                destination_amount = None
        else:
            logger.warning("Reloadly fx-rate failed: %s", fx_res.text)

        if destination_amount is None:
            try:
                fx_info = op_data.get("fx") or {}
                rate = fx_info.get("rate")
                if rate is not None:
                    destination_amount = normalized_amount * float(rate)
            except Exception:
                destination_amount = None

        if destination_amount is None:
            destination_amount = normalized_amount

        return {
            "destinationAmount": round(float(destination_amount), 2),
            "destinationCurrencyCode": local_currency,
        }

    except Exception as exc:
        logger.exception("Reloadly quote error: %s", exc)
        return None


# ---------------------------
# Send Data Topup
# ---------------------------

def send_data_topup(
    phone: str,
    plan_id: int,
    country_iso: str,
    custom_identifier: str | None = None,
) -> Dict[str, Any]:
    normalized_phone = _normalize_phone(phone)
    normalized_country = _normalize_country_iso(country_iso)

    if not normalized_phone:
        raise RuntimeError("Reloadly phone missing")

    if not normalized_country:
        raise RuntimeError("Reloadly country ISO missing")

    try:
        normalized_plan_id = int(plan_id)
    except Exception as exc:
        raise RuntimeError("Invalid plan id") from exc

    if normalized_plan_id <= 0:
        raise RuntimeError("Invalid plan id")

    operator_data = _lookup_operator(normalized_phone, normalized_country)

    token = get_reloadly_token()
    headers = _build_headers(token)

    url = f"{RELOADLY_V1_URL}/topups"

    payload = {
        "operatorId": operator_data["operator_id"],
        "productId": normalized_plan_id,
        "customIdentifier": str(custom_identifier or "").strip() or None,
        "recipientPhone": {
            "countryCode": operator_data["country_code"],
            "number": _extract_local_number(normalized_phone),
        },
    }

    if not payload["customIdentifier"]:
        payload.pop("customIdentifier", None)

    res = _request_with_token_refresh(
        "POST",
        url,
        headers=headers,
        json=payload,
        timeout=20,
    )

    if res.status_code not in (200, 201):
        raise RuntimeError(f"Reloadly DATA topup failed: {_extract_error_message(res)}")

    data = _safe_json(res)
    if not isinstance(data, dict):
        raise RuntimeError("Invalid Reloadly DATA response")

    transaction_id = data.get("transactionId")
    returned_custom_id = data.get("customIdentifier") or payload.get("customIdentifier")

    return {
        "transaction_id": transaction_id,
        "custom_id": returned_custom_id,
        "status": _normalize_status(data.get("status")) if data.get("status") else "PROCESSING",
        "operator_id": data.get("operatorId") or operator_data["operator_id"],
        "raw": data,
    }