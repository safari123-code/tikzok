# ---------------------------
# Feature: Recharge Routes
# ---------------------------

from __future__ import annotations

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from services.payment.currency_service import CurrencyService
from services.payment.fees_service import FeesService
from services.recharge.recharge_service import (
    detect_country_iso_from_phone,
    is_phone_length_valid,
    normalize_phone_e164_light,
)
from services.reloadly.airtime_service import get_topup_status
from services.reloadly.data_service import (
    get_reloadly_plans,
    get_reloadly_quote,
)
from services.reloadly.operators_service import (
    get_reloadly_operator_amounts,
    get_reloadly_operators_by_country,
    lookup_phone_number,
)
from services.reloadly.transaction_service import (
    TransactionServiceError,
    build_transaction_reference,
    process_recharge,
    refresh_transaction_status,
)

logger = logging.getLogger(__name__)

recharge_bp = Blueprint("recharge", __name__, url_prefix="/recharge")

# Compat ancien code
get_reloadly_operator_auto_detect = lookup_phone_number


# ---------------------------
# Helpers
# ---------------------------

def get_city_for_country(iso):
    file_path = Path("static/data/country_cities.json")

    if not file_path.exists():
        return "default"

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return "default"

    return data.get((iso or "").upper(), "default")


def _session_operator():
    operator = session.get("recharge_operator") or {}
    return operator if isinstance(operator, dict) else {}


def _get_payment_reference() -> str:
    """
    Remplace dès que possible par ta vraie source Stripe :
    - payment_intent_id
    - checkout_session_id
    - internal order id
    """
    candidates = [
        session.get("stripe_payment_intent_id"),
        session.get("payment_intent_id"),
        session.get("checkout_session_id"),
        session.get("order_id"),
        session.get("recharge_payment_reference"),
    ]

    for value in candidates:
        if value:
            return str(value)

    # fallback compat
    phone = session.get("recharge_phone") or ""
    amount = session.get("recharge_amount") or ""
    forfait = session.get("recharge_forfait") or {}
    forfait_id = forfait.get("id") if isinstance(forfait, dict) else ""

    fallback = f"fallback:{phone}:{amount}:{forfait_id}"
    return fallback


# ---------------------------
# Select Forfait (FINAL FIXED)
# ---------------------------

@recharge_bp.get("/select-forfait")
def select_forfait_get():

    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone)
    operator = _session_operator()

    # ---------------------------
    # Operator detection
    # ---------------------------
    if not operator:
        detected = get_reloadly_operator_auto_detect(phone, country_iso) or {}

        if detected:
            operator = {
                "id": detected.get("id") or detected.get("operatorId"),
                "name": detected.get("name"),
                "logo_url": detected.get("logo_url"),
                "country_iso": detected.get("country_iso") or country_iso,

                # 🔥 FIX IMPORTANT (toujours bool propre)
                "supports_data": bool(
                    detected.get("data")
                    or detected.get("supportsData")
                    or detected.get("bundle")
                )
            }

            session["recharge_operator"] = operator

    logger.info("📡 OPERATOR: %s", operator)

    # ---------------------------
    # Get plans
    # ---------------------------
    plans = []

    operator_id = (
        operator.get("id")
        or operator.get("operatorId")
        or operator.get("operator_id")
    )

    if operator_id:
        plans = get_reloadly_plans(operator)

    logger.info("📦 DATA PLANS COUNT: %s", len(plans))
    logger.info("🔥 SUPPORTS DATA: %s", operator.get("supports_data"))

    # ---------------------------
    # 🔥 UX SMART (IMPORTANT)
    # ---------------------------

    # CAS 1 → pas de data DU TOUT
    if operator and operator.get("supports_data") is False:
        return redirect(url_for("recharge.select_amount_get"))

    # CAS 2 → data possible mais API vide
    if not plans:
        logger.warning("⚠️ No plans but operator supports data")

        return render_template(
            "recharge/select_forfait.html",
            plans=[],
            operator=operator,
            phone=phone,
            no_plans=True
        )

    # ---------------------------
    # Normal flow
    # ---------------------------
    return render_template(
        "recharge/select_forfait.html",
        plans=plans,
        operator=operator,
        phone=phone,
        no_plans=False
    )
# ---------------------------
# Select Forfait (POST)
# ---------------------------

@recharge_bp.post("/select-forfait")
def select_forfait_post():
    data = request.get_json(silent=True) or {}

    gb = data.get("gb")
    price = data.get("price")
    plan_id = data.get("id")

    if not gb or not price or not plan_id:
        return jsonify({"ok": False}), 400

    session["recharge_forfait"] = {
        "id": int(plan_id),
        "gb": gb,
        "price": price,
    }

    return jsonify({"ok": True})


# ---------------------------
# API Phone Lookup
# ---------------------------

@recharge_bp.route("/api/lookup-number", methods=["POST"])
def lookup_number():
    data = request.get_json(silent=True) or {}

    phone = normalize_phone_e164_light(data.get("phone"))
    country = (data.get("country") or "").strip().upper()

    if not phone or not is_phone_length_valid(phone) or not country:
        return jsonify({"valid": False}), 400

    result = lookup_phone_number(phone, country)

    if not result:
        return jsonify({"valid": False})

    session["recharge_operator"] = result

    return jsonify(
        {
            "valid": True,
            "operatorId": result.get("id"),
            "operatorName": result.get("name"),
            "logoUrl": result.get("logo_url"),
            "countryCode": result.get("country_iso"),
        }
    )


# ---------------------------
# Enter number (GET)
# ---------------------------

@recharge_bp.get("/enter-number")
def enter_number_get():
    initial_phone = session.get("recharge_phone", "+93")
    country_iso = detect_country_iso_from_phone(initial_phone) or "AF"
    city = get_city_for_country(country_iso)

    return render_template(
        "recharge/enter_number.html",
        initial_phone=initial_phone,
        country_iso=country_iso,
        city=city,
    )


# ---------------------------
# Enter number (POST)
# ---------------------------

@recharge_bp.post("/enter-number")
def enter_number_post():
    raw = request.form.get("phone", "")
    phone = normalize_phone_e164_light(raw)

    country_iso = (
        request.form.get("country_iso")
        or detect_country_iso_from_phone(phone)
        or "AF"
    )

    if not phone or not is_phone_length_valid(phone):
        city = get_city_for_country(country_iso)

        return render_template(
            "recharge/enter_number.html",
            initial_phone=phone or "+93",
            country_iso=country_iso,
            city=city,
            phone_error=True,
        ), 400

    session["recharge_phone"] = phone
    session["country_iso"] = country_iso.upper()

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select Operator (GET)
# ---------------------------

@recharge_bp.get("/select-operator")
def select_operator_get():
    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone) or "FR"
    operators = get_reloadly_operators_by_country(country_iso)

    return render_template(
        "recharge/select_operator.html",
        operators=operators,
        phone=phone,
    )


# ---------------------------
# Select Operator (POST)
# ---------------------------

@recharge_bp.route("/select-operator", methods=["POST"])
def select_operator_post():
    operator_id = request.form.get("operator_id")
    operator_name = request.form.get("operator_name")
    operator_logo = request.form.get("operator_logo")
    country_name = request.form.get("country_name")
    country_iso = request.form.get("country_iso") or session.get("country_iso")
    supports_data = str(request.form.get("supports_data")).lower() == "true"

    if not operator_id:
        return redirect(url_for("recharge.select_operator_get"))

    session["recharge_operator"] = {
        "id": int(operator_id),
        "name": operator_name,
        "logo_url": operator_logo,
        "country_name": country_name,
        "country_iso": country_iso,
        "supports_data": supports_data,
    }

    if supports_data:
        return redirect(url_for("recharge.select_forfait_get"))

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Feature: Select amount (GET)
# ---------------------------

@recharge_bp.get("/select-amount")
def select_amount_get():
    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone) or "FR"
    operator = _session_operator()

    # ---------------------------
    # Operator detection
    # ---------------------------
    if not operator:
        operator = get_reloadly_operator_auto_detect(phone, country_iso) or {}
        if operator:
            session["recharge_operator"] = operator

    operator_id = operator.get("id")

    # ---------------------------
    # Amounts
    # ---------------------------
    operator_amounts = {
        "fixedAmounts": [],
        "minAmount": 2,
        "maxAmount": 50,
    }

    if operator_id:
        operator_amounts = get_reloadly_operator_amounts(operator_id) or operator_amounts

    # ---------------------------
    # Currency & Fees
    # ---------------------------
    currency = CurrencyService.currency_from_phone(phone)
    tax_rate = FeesService.get_tax_rate(currency)

    operator["currency_code"] = currency

    # ✅ NOUVEAU : devise reçue (RELOADLY)
    destination_currency = operator.get("destinationCurrencyCode")

    try:
        amount = float(session.get("recharge_amount", 5.00))
    except Exception:
        amount = 5.00

    breakdown = FeesService.breakdown(amount, currency)

    # ---------------------------
    # Quote
    # ---------------------------
    quote = None

    if operator_id:
        quote = get_reloadly_quote(
            operator_id=operator_id,
            amount=amount,
            phone=phone,
            country_iso=country_iso,
        )

    # ---------------------------
    # Received
    # ---------------------------
    received_display = CurrencyService.received_display_value(
        phone=phone,
        amount=amount,
        selected_forfait=session.get("recharge_forfait"),
        quote=quote,
    )

    # ---------------------------
    # Template
    # ---------------------------
    return render_template(
        "recharge/select_amount.html",
        phone=phone,
        country_iso=country_iso,
        operator=operator,
        amounts=operator_amounts,
        tax_rate=breakdown["tax_rate"],
        amount=breakdown["amount"],
        tax=breakdown["tax"],
        total=breakdown["total"],
        currency_code=currency,
        received_display=received_display,

        # ✅ AJOUT IMPORTANT
        destination_currency=destination_currency,
    )


# ---------------------------
# Select amount (POST)
# ---------------------------

@recharge_bp.post("/select-amount")
def select_amount_post():

        # 🔒 LOGIN CHECK (AJOUT)
    if not session.get("user_id"):
        return redirect(url_for("auth.login", next=request.path))
    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    amount = request.form.get("amount")

    try:
        amount = float(amount)
    except Exception:
        return redirect(url_for("recharge.select_amount_get"))

    # ---------------------------
    # Feature: Amount validation (FINAL)
    # ---------------------------

    MIN_AMOUNT = 2.0
    MAX_AMOUNT = 40.0

    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        return redirect(url_for("recharge.select_amount_get"))

    # clamp sécurisé
    amount = max(MIN_AMOUNT, min(MAX_AMOUNT, amount))

    # ---------------------------
    # Currency & breakdown
    # ---------------------------

    currency = CurrencyService.currency_from_phone(phone)
    breakdown = FeesService.breakdown(amount, currency)

    # ---------------------------
    # Session
    # ---------------------------

    session["recharge_amount"] = str(amount)
    session["recharge_total_amount"] = str(breakdown["total"])

    return redirect(url_for("payment.card_get"))


# ---------------------------
# Execute Topup
# ---------------------------

@recharge_bp.post("/execute")
def execute_recharge():
    phone = session.get("recharge_phone")
    amount = session.get("recharge_amount")
    country_iso = session.get("country_iso")
    forfait = session.get("recharge_forfait")
    operator = _session_operator()

    if not phone or not country_iso:
        return jsonify({"ok": False, "message": "Session invalide"}), 400

    try:
        payment_reference = _get_payment_reference()

        result = process_recharge(
            payment_reference=payment_reference,
            phone=phone,
            country_iso=country_iso,
            amount=float(amount) if amount and not forfait else None,
            plan_id=int(forfait.get("id")) if forfait else None,
            operator_id=operator.get("id") if operator else None,
            user_id=session.get("user_id"),
            metadata={"flow": "recharge_route"},
        )

        session["last_transaction_id"] = result.transaction_id
        session["last_transaction_reference"] = result.custom_identifier

        return jsonify(
            {
                "ok": result.ok or result.status == "PROCESSING",
                "transaction_id": result.transaction_id,
                "status": result.status,
                "reference": result.custom_identifier,
                "duplicate": result.is_duplicate,
            }
        )

    except TransactionServiceError as exc:
        logger.exception("Topup transaction error: %s", exc)
        return jsonify({"ok": False, "message": str(exc)}), 500


# ---------------------------
# Status
# ---------------------------

@recharge_bp.get("/status")
def recharge_status():
    tx = session.get("last_transaction_id")
    reference = session.get("last_transaction_reference")

    if not tx and not reference:
        return jsonify({"ok": False, "message": "No transaction found"}), 404

    try:
        result = refresh_transaction_status(
            reference=reference or build_transaction_reference(
                payment_reference=_get_payment_reference(),
                phone=session.get("recharge_phone"),
                amount=session.get("recharge_amount"),
                plan_id=(session.get("recharge_forfait") or {}).get("id"),
                operator_id=(_session_operator() or {}).get("id"),
                country_iso=session.get("country_iso"),
            ),
            transaction_id=tx,
        )

        session["last_transaction_id"] = result.transaction_id

        return jsonify(
            {
                "ok": True,
                "status": result.status,
                "transaction_id": result.transaction_id,
                "reference": result.custom_identifier,
            }
        )

    except Exception as exc:
        logger.exception("Recharge status error: %s", exc)
        return jsonify({"ok": False, "message": "Status unavailable"}), 500


# ---------------------------
# AJAX Quote (FINAL PRODUCTION)
# ---------------------------

@recharge_bp.post("/api/quote")
def api_quote():
    phone = session.get("recharge_phone")
    operator = _session_operator()
    country_iso = session.get("country_iso") or "FR"

    if not phone or not operator:
        return jsonify({"ok": False}), 401

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    try:
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False}), 400

    # ---------------------------
    # Feature: Amount validation (SECURE)
    # ---------------------------

    MIN_AMOUNT = 2.0
    MAX_AMOUNT = 40.0

    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        return jsonify({
            "ok": False,
            "error": "invalid_amount",
            "min": MIN_AMOUNT,
            "max": MAX_AMOUNT
        }), 400

    # clamp sécurité
    amount = max(MIN_AMOUNT, min(MAX_AMOUNT, amount))

    operator_id = operator.get("id")

    # ---------------------------
    # Quote
    # ---------------------------

    quote = None

    if operator_id:
        quote = get_reloadly_quote(
            operator_id=operator_id,
            amount=amount,
            phone=phone,
            country_iso=country_iso,
        )

    # log propre (prod)
    logger.info("Reloadly quote: %s", quote)

    # ---------------------------
    # Currency
    # ---------------------------

    currency = None

    if quote:
        currency = (
            quote.get("destinationCurrencyCode")
            or quote.get("currencyCode")
        )

    if not currency:
        currency = operator.get("destinationCurrencyCode") or "EUR"

    # ---------------------------
    # Received
    # ---------------------------

    received = None

    if quote and quote.get("destinationAmount"):
        received = f"{quote['destinationAmount']:.2f} {currency}"

    if not received:
        received = "—"

    # ---------------------------
    # Response
    # ---------------------------

    return jsonify({
        "ok": True,
        "received": received,
        "destinationCurrency": currency,
        "min": MIN_AMOUNT,
        "max": MAX_AMOUNT
    })