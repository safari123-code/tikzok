# ---------------------------
# Feature: Reloadly Transaction Service
# ---------------------------

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from services.reloadly.airtime_service import get_topup_status, send_topup
from services.reloadly.data_service import send_data_topup


# ---------------------------
# Exceptions
# ---------------------------

class TransactionServiceError(Exception):
    pass


class DuplicateTransactionError(TransactionServiceError):
    pass


class InvalidTransactionInputError(TransactionServiceError):
    pass


class PaymentReferenceMissingError(TransactionServiceError):
    pass


# ---------------------------
# Result model
# ---------------------------

@dataclass
class TransactionResult:
    ok: bool
    status: str
    transaction_id: Optional[int] = None
    custom_identifier: Optional[str] = None
    is_duplicate: bool = False
    message: str = ""
    raw: Optional[Dict[str, Any]] = None


# ---------------------------
# In-memory store fallback
# ---------------------------

_MEM_STORE: Dict[str, Dict[str, Any]] = {}
_MEM_LOCKS: Dict[str, threading.Lock] = {}
_GLOBAL_LOCK = threading.Lock()


def _get_lock(key: str) -> threading.Lock:
    with _GLOBAL_LOCK:
        if key not in _MEM_LOCKS:
            _MEM_LOCKS[key] = threading.Lock()
        return _MEM_LOCKS[key]


# ---------------------------
# Helpers
# ---------------------------

def build_transaction_reference(
    *,
    payment_reference: str,
    phone: str,
    amount: float | None = None,
    plan_id: int | None = None,
    operator_id: int | None = None,
    country_iso: str | None = None,
) -> str:
    payment_reference = str(payment_reference or "").strip()
    phone = str(phone or "").strip()
    country_iso = str(country_iso or "").strip().upper()

    if not payment_reference:
        raise PaymentReferenceMissingError("payment_reference manquant")

    if not phone:
        raise InvalidTransactionInputError("phone manquant")

    raw = "|".join(
        [
            payment_reference,
            phone,
            str(amount if amount is not None else ""),
            str(plan_id if plan_id is not None else ""),
            str(operator_id if operator_id is not None else ""),
            country_iso,
        ]
    )

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"tkz_tx_{digest[:40]}"


def normalize_reloadly_status(status: str | None) -> str:
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


def _mem_find(reference: str) -> Optional[Dict[str, Any]]:
    return _MEM_STORE.get(reference)


def _mem_create_pending(payload: Dict[str, Any]) -> None:
    _MEM_STORE[payload["reference"]] = dict(payload)


def _mem_mark_processing(reference: str, payload: Optional[Dict[str, Any]] = None) -> None:
    item = _MEM_STORE.get(reference, {"reference": reference})
    item["status"] = "PROCESSING"
    item["updated_at"] = int(time.time())
    if payload:
        item.update(payload)
    _MEM_STORE[reference] = item


def _mem_mark_success(reference: str, payload: Optional[Dict[str, Any]] = None) -> None:
    item = _MEM_STORE.get(reference, {"reference": reference})
    item["status"] = "SUCCESS"
    item["updated_at"] = int(time.time())
    if payload:
        item.update(payload)
    _MEM_STORE[reference] = item


def _mem_mark_failed(reference: str, payload: Optional[Dict[str, Any]] = None) -> None:
    item = _MEM_STORE.get(reference, {"reference": reference})
    item["status"] = "FAILED"
    item["updated_at"] = int(time.time())
    if payload:
        item.update(payload)
    _MEM_STORE[reference] = item


def _validate_inputs(
    *,
    phone: str,
    country_iso: str,
    amount: float | None,
    plan_id: int | None,
) -> None:
    if not phone:
        raise InvalidTransactionInputError("phone manquant")

    if not country_iso:
        raise InvalidTransactionInputError("country_iso manquant")

    if plan_id is not None:
        return

    if amount is None:
        raise InvalidTransactionInputError("amount manquant")

    try:
        amount = float(amount)
    except Exception as exc:
        raise InvalidTransactionInputError("amount invalide") from exc

    if amount <= 0:
        raise InvalidTransactionInputError("amount doit être > 0")


# ---------------------------
# Execute recharge
# ---------------------------

def process_recharge(
    *,
    payment_reference: str,
    phone: str,
    country_iso: str,
    amount: float | None = None,
    plan_id: int | None = None,
    operator_id: int | None = None,
    user_id: Any | None = None,
    metadata: Optional[Dict[str, Any]] = None,
    repo_find: Callable[[str], Optional[Dict[str, Any]]] = _mem_find,
    repo_create_pending: Callable[[Dict[str, Any]], None] = _mem_create_pending,
    repo_mark_processing: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_processing,
    repo_mark_success: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_success,
    repo_mark_failed: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_failed,
) -> TransactionResult:
    _validate_inputs(
        phone=phone,
        country_iso=country_iso,
        amount=amount,
        plan_id=plan_id,
    )

    reference = build_transaction_reference(
        payment_reference=payment_reference,
        phone=phone,
        amount=amount,
        plan_id=plan_id,
        operator_id=operator_id,
        country_iso=country_iso,
    )

    lock = _get_lock(reference)

    with lock:
        existing = repo_find(reference)

        if existing:
            existing_status = normalize_reloadly_status(existing.get("status"))

            if existing_status in {"SUCCESS", "PROCESSING"}:
                return TransactionResult(
                    ok=(existing_status == "SUCCESS"),
                    status=existing_status,
                    transaction_id=existing.get("reloadly_transaction_id"),
                    custom_identifier=reference,
                    is_duplicate=True,
                    message="Transaction déjà traitée ou en cours",
                    raw=existing,
                )

        payload = {
            "reference": reference,
            "status": "PENDING",
            "phone": phone,
            "country_iso": country_iso,
            "amount": float(amount) if amount is not None else None,
            "plan_id": int(plan_id) if plan_id is not None else None,
            "operator_id": int(operator_id) if operator_id is not None else None,
            "user_id": user_id,
            "metadata": metadata or {},
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }

        if not existing:
            repo_create_pending(payload)

        repo_mark_processing(reference, None)

        try:
            if plan_id is not None:
                raw_result = send_data_topup(
                    phone=phone,
                    plan_id=int(plan_id),
                    country_iso=country_iso,
                    custom_identifier=reference,
                )
            else:
                raw_result = send_topup(
                    phone=phone,
                    amount=float(amount),
                    country_iso=country_iso,
                    custom_identifier=reference,
                )

            reloadly_transaction_id = raw_result.get("transaction_id")
            raw_status = normalize_reloadly_status(raw_result.get("status"))

            if raw_status == "UNKNOWN":
                raw_status = "PROCESSING"

            if raw_status in {"SUCCESS", "PROCESSING"}:
                repo_mark_success(
                    reference,
                    {
                        "status": raw_status,
                        "reloadly_transaction_id": reloadly_transaction_id,
                        "custom_identifier": reference,
                        "reloadly_raw": raw_result,
                    },
                )

                return TransactionResult(
                    ok=(raw_status == "SUCCESS"),
                    status=raw_status,
                    transaction_id=reloadly_transaction_id,
                    custom_identifier=reference,
                    is_duplicate=False,
                    message="Recharge exécutée",
                    raw=raw_result,
                )

            repo_mark_failed(
                reference,
                {
                    "status": raw_status,
                    "reloadly_transaction_id": reloadly_transaction_id,
                    "custom_identifier": reference,
                    "reloadly_raw": raw_result,
                },
            )

            return TransactionResult(
                ok=False,
                status=raw_status,
                transaction_id=reloadly_transaction_id,
                custom_identifier=reference,
                is_duplicate=False,
                message="Recharge non aboutie",
                raw=raw_result,
            )

        except Exception as exc:
            repo_mark_failed(
                reference,
                {
                    "status": "FAILED",
                    "custom_identifier": reference,
                    "error": str(exc),
                },
            )
            raise TransactionServiceError(str(exc)) from exc


# ---------------------------
# Refresh status
# ---------------------------

def refresh_transaction_status(
    *,
    reference: str,
    transaction_id: int | None,
    repo_find: Callable[[str], Optional[Dict[str, Any]]] = _mem_find,
    repo_mark_success: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_success,
    repo_mark_failed: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_failed,
    repo_mark_processing: Callable[[str, Optional[Dict[str, Any]]], None] = _mem_mark_processing,
) -> TransactionResult:
    if not reference:
        raise InvalidTransactionInputError("reference manquante")

    current = repo_find(reference)

    if not current and not transaction_id:
        raise InvalidTransactionInputError("transaction introuvable")

    if not transaction_id and current:
        transaction_id = current.get("reloadly_transaction_id")

    if not transaction_id:
        return TransactionResult(
            ok=False,
            status="UNKNOWN",
            custom_identifier=reference,
            message="Aucun transaction_id Reloadly disponible",
            raw=current,
        )

    raw = get_topup_status(transaction_id)
    status = normalize_reloadly_status(raw.get("status"))

    payload = {
        "reloadly_transaction_id": transaction_id,
        "reloadly_status_raw": raw,
        "updated_at": int(time.time()),
    }

    if status == "SUCCESS":
        repo_mark_success(reference, {"status": status, **payload})
    elif status in {"FAILED", "REFUNDED"}:
        repo_mark_failed(reference, {"status": status, **payload})
    else:
        repo_mark_processing(reference, {"status": status, **payload})

    return TransactionResult(
        ok=(status == "SUCCESS"),
        status=status,
        transaction_id=transaction_id,
        custom_identifier=reference,
        message="Statut synchronisé",
        raw=raw,
    )


# ---------------------------
# Public helper
# ---------------------------

def get_existing_transaction(
    reference: str,
    repo_find: Callable[[str], Optional[Dict[str, Any]]] = _mem_find,
) -> Optional[Dict[str, Any]]:
    if not reference:
        return None
    return repo_find(reference)