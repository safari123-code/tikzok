# ---------------------------
# routes/recharge.py
# ---------------------------

import json
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.recharge_service import (
    normalize_phone_e164_light,
    is_phone_length_valid,
    detect_country_iso_from_phone,
    get_reloadly_operator_auto_detect,
    get_reloadly_operator_amounts,
    quote_local_amount
)

from services.reloadly_service import (
    get_reloadly_operators_by_country,
    lookup_phone_number,
    get_reloadly_plans
)

from services.currency_service import CurrencyService
from services.fees_service import FeesService
from services.reloadly_service import get_reloadly_quote

recharge_bp = Blueprint("recharge", __name__, url_prefix="/recharge")


# ---------------------------
# Select Forfait
# ---------------------------

@recharge_bp.get("/select-forfait")
def select_forfait_get():

    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone)

    operator = session.get("recharge_operator")

    if not operator:
        operator = get_reloadly_operator_auto_detect(phone, country_iso)

    plans = []

    if operator and operator.get("id"):
        plans = get_reloadly_plans(operator["id"])

    return render_template(
        "recharge/select_forfait.html",
        plans=plans,
        operator=operator,
        phone=phone
    )
# ---------------------------
# Select Forfait (POST)
# ---------------------------

@recharge_bp.post("/select-forfait")
def select_forfait_post():

    data = request.get_json(silent=True) or {}

    gb = data.get("gb")
    price = data.get("price")
    plan_id = data.get("id")  # 🔥 AJOUT CRITIQUE

    if not gb or not price or not plan_id:
        return jsonify({"ok": False}), 400

    session["recharge_forfait"] = {
        "id": plan_id,   # 🔥 IMPORTANT
        "gb": gb,
        "price": price
    }

    return jsonify({"ok": True})

# ---------------------------
# Country → City mapping
# ---------------------------

def get_city_for_country(iso):

    file = Path("static/data/country_cities.json")

    if not file.exists():
        return "default"

    try:
        data = json.loads(file.read_text())
    except Exception:
        return "default"

    return data.get((iso or "").upper(), "default")


# ---------------------------
# API Phone Lookup
# ---------------------------

@recharge_bp.route("/api/lookup-number", methods=["POST"])
def lookup_number():

    data = request.get_json(silent=True) or {}

    phone = data.get("phone")
    country = data.get("country")

    result = lookup_phone_number(phone, country)

    if not result:
        return jsonify({"valid": False})

    # sauvegarder l'opérateur détecté
    session["recharge_operator"] = {
        "id": result.get("operatorId"),
        "name": result.get("name"),
        "logo_url": result.get("logoUrl"),
        "country": result.get("countryName")
    }

    return jsonify({
        "valid": True,
        "operatorId": result.get("operatorId"),
        "operatorName": result.get("name"),
        "logoUrl": result.get("logoUrl"),
        "countryCode": result.get("countryCode")
    })


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
        city=city
    )


# ---------------------------
# Enter number (POST)
# ---------------------------
@recharge_bp.post("/enter-number")
def enter_number_post():

    raw = request.form.get("phone", "")
    phone = normalize_phone_e164_light(raw)

    # ---------------------------
    # Detect country (IMPORTANT)
    # ---------------------------
    country_iso = (
        request.form.get("country_iso")  # priorité form
        or detect_country_iso_from_phone(phone)
        or "AF"
    )

    # ---------------------------
    # Validation
    # ---------------------------
    if not phone or not is_phone_length_valid(phone):

        city = get_city_for_country(country_iso)

        return render_template(
            "recharge/enter_number.html",
            initial_phone=phone or "+93",
            country_iso=country_iso,
            city=city,
            phone_error=True,
        ), 400

    # ---------------------------
    # SAVE SESSION (IMPORTANT)
    # ---------------------------
    session["recharge_phone"] = phone
    session["country_iso"] = country_iso.upper() # 🔥 clé admin

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
        phone=phone
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

    supports_data = str(request.form.get("supports_data")).lower() == "true"

    if not operator_id:
        return redirect(url_for("recharge.select_operator_get"))

    session["recharge_operator"] = {
        "id": operator_id,
        "name": operator_name,
        "logo_url": operator_logo,
        "country": country_name,
        "supports_data": supports_data
    }

    # 🔥 LOGIQUE PRODUIT
    if supports_data:
        return redirect(url_for("recharge.select_forfait_get"))

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select amount (GET) - FINAL PRO
# ---------------------------
@recharge_bp.get("/select-amount")
def select_amount_get():

    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone) or "FR"

    operator = session.get("recharge_operator")

    if not operator:
        operator = get_reloadly_operator_auto_detect(
            phone=phone,
            country_iso=country_iso,
        ) or {}

    # ---------------------------
    # Operator amounts (SAFE)
    # ---------------------------
    operator_amounts = {}

    operator_id = operator.get("id")
    print("📡 OPERATOR ID:", operator_id)

    if operator_id:
        try:
            operator_amounts = get_reloadly_operator_amounts(
                operator_id=operator_id
            ) or {}

            print("📡 Operator amounts loaded:", bool(operator_amounts))

        except Exception as e:
            print("❌ Operator amounts error:", e)
            operator_amounts = {}
    else:
        print("⚠️ No operator detected → fallback mode")

    # ---------------------------
    # Currency + fees
    # ---------------------------
    currency = CurrencyService.currency_from_phone(phone)
    rate = CurrencyService.rate_from_currency(currency)
    tax_rate = FeesService.get_tax_rate(currency)

    operator["currency_code"] = currency

    amount = float(session.get("recharge_amount", 5.00))

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

    # ---------------------------
    # BUSINESS: compute payout (interne uniquement)
    # ---------------------------
    fees = FeesService.compute_payout(amount, currency)
    payout_amount = fees["payout"]

    print("💰 Payout:", payout_amount)

    # ---------------------------
    # Reloadly quote (FIX PRODUCTION)
    # ---------------------------
    quote = None

    if operator_id:
        try:
            print("📡 Using operator for quote:", operator_id)

            # ✅ IMPORTANT : Reloadly utilise le montant brut
            quote = get_reloadly_quote(
                operator_id=operator_id,
                amount=amount
            )

            print("📡 Reloadly quote:", quote)

        except Exception as e:
            print("❌ Quote error:", e)
            quote = None
    else:
        print("⚠️ Skip quote → no operator")

    # ---------------------------
    # FINAL DISPLAY (BUSINESS CONTROL)
    # ---------------------------
    if quote and quote.get("localAmount"):
        received_display = f"{int(float(quote['localAmount']))} {quote.get('localCurrency', '')}"
    else:
        # ✅ utilise amount (PAS payout)
        local, cur = CurrencyService.estimate_local_amount(phone, amount)
        received_display = f"{local} {cur}"

    return render_template(
        "recharge/select_amount.html",
        phone=phone,
        country_iso=country_iso,
        operator=operator,
        amounts=operator_amounts,
        tax_rate=tax_rate,
        amount=amount,
        tax=tax,
        total=total,
        currency_code=currency,
        currency_rate=rate,
        received_display=received_display
    )
# ---------------------------
# Select amount (POST)
# ---------------------------

@recharge_bp.post("/select-amount")
def select_amount_post():

    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    amount = request.form.get("amount")

    try:
        amount = float(amount)
    except Exception:
        return redirect(url_for("recharge.select_amount_get"))

    amount = max(1.0, min(1000.0, amount))

    currency = CurrencyService.currency_from_phone(phone)
    tax_rate = FeesService.get_tax_rate(currency)

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

    session["recharge_amount"] = str(amount)
    session["recharge_total_amount"] = str(total)

    return redirect(url_for("payment.method_get"))


# ---------------------------
# AJAX: quote (Currency PRO)
# ---------------------------

@recharge_bp.post("/api/quote")
def api_quote():

    phone = session.get("recharge_phone")

    if not phone:
        return jsonify({"ok": False}), 401

    data = request.get_json(silent=True) or {}

    amount = data.get("amount")

    try:
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False}), 400

    # 🔥 utilise TON CurrencyService (clé du problème)
    received = CurrencyService.received_display_value(
        phone=phone,
        amount=amount,
        selected_forfait=session.get("recharge_forfait"),
        quote=None  # ❌ on ignore Reloadly
    )

    return jsonify({
        "ok": True,
        "received": received
    })


# ---------------------------
# Store total before payment
# ---------------------------

@recharge_bp.post("/api/store-total")
def api_store_total():

    data = request.get_json(silent=True) or {}

    total = data.get("total")

    try:
        total = float(total)
    except Exception:
        return jsonify({"ok": False}), 400

    total = max(1.0, min(1000.0, total))

    session["recharge_total_amount"] = str(total)

    return jsonify({"ok": True})

# ---------------------------
# Execute Topup (POST)
# ---------------------------
from services.reloadly_service import send_topup, send_data_topup


@recharge_bp.post("/execute")
def execute_recharge():

    phone = session.get("recharge_phone")
    amount = session.get("recharge_amount")
    country_iso = session.get("country_iso")
    forfait = session.get("recharge_forfait")  # 🔥 IMPORTANT

    if not phone:
        return jsonify({"ok": False, "error": "missing phone"}), 400

    try:
        # ---------------------------
        # DATA FLOW
        # ---------------------------
        if forfait:
            plan_id = forfait.get("id")  # ⚠️ il faut stocker ça côté frontend

            if not plan_id:
                return jsonify({"ok": False, "error": "missing plan"}), 400

            result = send_data_topup(
                phone=phone,
                plan_id=int(plan_id),
                country_iso=country_iso
            )

        # ---------------------------
        # AIRTIME FLOW
        # ---------------------------
        else:
            if not amount:
                return jsonify({"ok": False, "error": "missing amount"}), 400

            amount = float(amount)

            result = send_topup(
                phone=phone,
                amount=amount,
                country_iso=country_iso
            )

        # ---------------------------
        # Save transaction
        # ---------------------------
        session["last_transaction_id"] = result["transaction_id"]

        return jsonify({
            "ok": True,
            "transaction_id": result["transaction_id"]
        })

    except Exception as e:
        print("Topup error:", e)

        return jsonify({
            "ok": False,
            "error": "topup_failed"
        }), 500
    
# ---------------------------
# Check Topup Status
# ---------------------------
from services.reloadly_service import get_topup_status


@recharge_bp.get("/status")
def recharge_status():

    transaction_id = session.get("last_transaction_id")

    if not transaction_id:
        return jsonify({"ok": False}), 400

    try:
        result = get_topup_status(transaction_id)

        return jsonify({
            "ok": True,
            "status": result["status"]
        })

    except Exception as e:
        print("Status error:", e)

        return jsonify({
            "ok": False
        }), 500

# ---------------------------
# API: Operators list (Reloadly)
# ---------------------------

@recharge_bp.get("/api/operators")
def api_operators():

    phone = session.get("recharge_phone")

    if not phone:
        return jsonify({"ok": False}), 401

    country_iso = detect_country_iso_from_phone(phone) or "FR"

    operators = get_reloadly_operators_by_country(country_iso)

    return jsonify({
        "ok": True,
        "operators": operators
    })