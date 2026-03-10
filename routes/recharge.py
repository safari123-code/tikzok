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

from services.reloadly_service import get_reloadly_operators_by_country
from services.currency_service import CurrencyService
from services.fees_service import FeesService

recharge_bp = Blueprint("recharge", __name__, url_prefix="/recharge")


# ---------------------------
# Select Forfait
# ---------------------------

@recharge_bp.get("/select-forfait")
def select_forfait_get():
    return render_template("recharge/select_forfait.html")


@recharge_bp.post("/select-forfait")
def select_forfait_post():

    data = request.get_json()

    session["recharge_forfait"] = {
        "gb": data.get("gb"),
        "price": data.get("price")
    }

    return {"success": True}


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

    if not phone or not is_phone_length_valid(phone):

        country_iso = detect_country_iso_from_phone(phone) or "AF"
        city = get_city_for_country(country_iso)

        return render_template(
            "recharge/enter_number.html",
            initial_phone=phone or "+93",
            country_iso=country_iso,
            city=city,
            phone_error=True,
        ), 400

    session["recharge_phone"] = phone

    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select Operator
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


@recharge_bp.post("/select-operator")
def select_operator_post():

    session["recharge_operator"] = {
        "id": request.form.get("operator_id"),
        "name": request.form.get("operator_name"),
        "logo_url": request.form.get("operator_logo"),
        "country": request.form.get("country_name")
    }

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

    # operator choisi par utilisateur
    operator = session.get("recharge_operator")

    # fallback auto detect
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

    # ---------------------------
    # Secure total calculation
    # ---------------------------

    currency = CurrencyService.currency_from_phone(phone)
    tax_rate = FeesService.get_tax_rate(currency)

    tax = round(amount * tax_rate, 2)
    total = round(amount + tax, 2)

    # on garde aussi le montant brut si besoin
    session["recharge_amount"] = str(amount)

    # total réel utilisé pour le paiement
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