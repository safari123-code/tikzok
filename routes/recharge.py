# ---------------------------
# routes/recharge.py (FINAL CLEAN SERVICES)
# ---------------------------

import json
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

# ---------------------------
# Recharge core
# ---------------------------
from services.recharge.recharge_service import (
    normalize_phone_e164_light,
    is_phone_length_valid,
    detect_country_iso_from_phone,
    quote_local_amount
)

# ---------------------------
# Reloadly (NEW ARCHITECTURE)
# ---------------------------
from services.reloadly.airtime_service import send_topup, get_topup_status
from services.reloadly.data_service import send_data_topup, get_reloadly_quote, get_reloadly_plans
from services.reloadly.operators_service import (
    get_reloadly_operators_by_country,
    lookup_phone_number,
    get_reloadly_operator_amounts
)

# 🔥 alias SAFE (compat ancien code)
get_reloadly_operator_auto_detect = lookup_phone_number

# ---------------------------
# Business services
# ---------------------------
from services.payment.currency_service import CurrencyService
from services.payment.fees_service import FeesService


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

    print("📡 OPERATOR:", operator)

    plans = []

    if operator and operator.get("id"):
        plans = get_reloadly_plans(operator["id"])

    print("📡 PLANS RAW:", plans)
    print("📡 PLANS COUNT:", len(plans) if plans else 0)

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
    plan_id = data.get("id")

    if not gb or not price or not plan_id:
        return jsonify({"ok": False}), 400

    session["recharge_forfait"] = {
        "id": plan_id,
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

    if supports_data:
        return redirect(url_for("recharge.select_forfait_get"))

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select amount (GET)
# ---------------------------
@recharge_bp.get("/select-amount")
def select_amount_get():

    # ---------------------------
    # Session / sécurité
    # ---------------------------
    phone = session.get("recharge_phone")

    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone) or "FR"

    # ---------------------------
    # Operator
    # ---------------------------
    operator = session.get("recharge_operator")

    if not operator:
        operator = get_reloadly_operator_auto_detect(
            phone,
            country_iso
        ) or {}

    operator_id = operator.get("id")

    # ---------------------------
    # Operator amounts
    # ---------------------------
    operator_amounts = {
        "fixedAmounts": [],
        "minAmount": 2,
        "maxAmount": 50
    }

    if operator_id:
        try:
            operator_amounts = get_reloadly_operator_amounts(
                operator_id
            ) or {}
        except Exception as e:
            print("❌ Operator amounts error:", e)

    # ---------------------------
    # Currency + fees
    # ---------------------------
    currency = CurrencyService.currency_from_phone(phone)
    tax_rate = FeesService.get_tax_rate(currency)

    operator["currency_code"] = currency

    # ---------------------------
    # Amount
    # ---------------------------
    try:
        amount = float(session.get("recharge_amount", 5.00))
    except Exception:
        amount = 5.00

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

    # ---------------------------
    # Reloadly quote (SAFE)
    # ---------------------------
    quote = None

    if operator_id:
        try:
            quote = get_reloadly_quote(
                operator_id=operator_id,
                amount=amount
            )
            print("QUOTE RESULT:", quote)
        except Exception as e:
            print("❌ Quote error:", e)
            quote = None

    # ---------------------------
    # FINAL DISPLAY (SOURCE = RELOADLY)
    # ---------------------------
    received_display = CurrencyService.received_display_value(
        phone=phone,
        amount=amount,
        selected_forfait=session.get("recharge_forfait"),
        quote=quote
    )

    # ---------------------------
    # Render
    # ---------------------------
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

    # 🔒 sécurité business
    amount = max(1.0, min(1000.0, amount))

    currency = CurrencyService.currency_from_phone(phone)
    tax_rate = FeesService.get_tax_rate(currency)

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

    # ---------------------------
    # SAVE SESSION
    # ---------------------------
    session["recharge_amount"] = str(amount)
    session["recharge_total_amount"] = str(total)

    return redirect(url_for("payment.method_get"))

# ---------------------------
# Execute Topup
# ---------------------------
@recharge_bp.post("/execute")
def execute_recharge():

    phone = session.get("recharge_phone")
    amount = session.get("recharge_amount")
    country_iso = session.get("country_iso")
    forfait = session.get("recharge_forfait")

    try:
        if forfait:
            result = send_data_topup(phone, forfait.get("id"), country_iso)
        else:
            result = send_topup(phone, float(amount), country_iso)

        session["last_transaction_id"] = result["transaction_id"]

        return jsonify({"ok": True, "transaction_id": result["transaction_id"]})

    except Exception as e:
        print("Topup error:", e)
        return jsonify({"ok": False}), 500


# ---------------------------
# Status
# ---------------------------
@recharge_bp.get("/status")
def recharge_status():

    tx = session.get("last_transaction_id")

    result = get_topup_status(tx)

    return jsonify({"ok": True, "status": result["status"]})

# ---------------------------
# AJAX Quote (FINAL SAFE + DEBUG)
# ---------------------------
@recharge_bp.post("/api/quote")
def api_quote():

    phone = session.get("recharge_phone")
    operator = session.get("recharge_operator")
    country_iso = session.get("country_iso")

    if not phone or not operator:
        return jsonify({"ok": False}), 401

    data = request.get_json(silent=True) or {}
    amount = data.get("amount")

    try:
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False}), 400

    operator_id = operator.get("id") or operator.get("operatorId")

    quote = None

    if operator_id:
        try:
            quote = get_reloadly_quote(
                operator_id=operator_id,
                amount=amount,
                phone=phone,
                country_iso=country_iso
            )

            # 🔥 DEBUG IMPORTANT
            print("📡 QUOTE RESULT:", quote)

        except Exception as e:
            print("❌ AJAX quote error:", e)
            quote = None

    # ---------------------------
    # SOURCE OF TRUTH
    # ---------------------------
    received = CurrencyService.received_display_value(
        phone=phone,
        amount=amount,
        selected_forfait=session.get("recharge_forfait"),
        quote=quote
    )

    # 🔥 DEBUG UI
    print("💰 RECEIVED DISPLAY:", received)

    return jsonify({
        "ok": True,
        "received": received
    })