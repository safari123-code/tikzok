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

    if not gb or not price:
        return jsonify({"ok": False}), 400

    # stocker forfait choisi
    session["recharge_forfait"] = {
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
# Select Operator
# ---------------------------

@recharge_bp.route("/select-operator", methods=["GET"])
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


@recharge_bp.route("/select-operator", methods=["POST"])
def select_operator_post():

    operator_id = request.form.get("operator_id")
    operator_name = request.form.get("operator_name")
    operator_logo = request.form.get("operator_logo")
    country_name = request.form.get("country_name")

    session["recharge_operator"] = {
        "id": operator_id,
        "name": operator_name,
        "logo_url": operator_logo,
        "country": country_name
    }

    if operator_name and "Data" in operator_name:
        return redirect(url_for("recharge.select_forfait_get"))

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select amount (GET)
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

    operator_amounts = {}

    if operator.get("id"):
        operator_amounts = get_reloadly_operator_amounts(
            operator_id=operator["id"]
        ) or {}

    currency = CurrencyService.currency_from_phone(phone)

    rate = CurrencyService.rate_from_currency(currency)

    tax_rate = FeesService.get_tax_rate(currency)

    operator["currency_code"] = currency

    amount = float(session.get("recharge_total_amount", 5.00))

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

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
        currency_rate=rate
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
# AJAX: quote Reloadly
# ---------------------------

@recharge_bp.post("/api/quote")
def api_quote():

    phone = session.get("recharge_phone")

    if not phone:
        return jsonify({"ok": False}), 401

    data = request.get_json(silent=True) or {}

    operator_id = data.get("operatorId")
    amount = data.get("amount")

    try:
        operator_id = int(operator_id)
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False}), 400

    q = quote_local_amount(
        operator_id=operator_id,
        amount=amount
    ) or {}

    return jsonify({"ok": True, **q})


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