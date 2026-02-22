from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.recharge_service import (
    normalize_phone_e164_light,
    is_phone_length_valid,
    detect_country_iso_from_phone,
    get_reloadly_operator_auto_detect,
    get_reloadly_operator_amounts,
    quote_local_amount,
)

recharge_bp = Blueprint("recharge", __name__, url_prefix="/recharge")


# ---------------------------
# Enter number
# ---------------------------
@recharge_bp.get("/enter-number")
def enter_number_get():
    initial_phone = session.get("recharge_phone", "+93")
    return render_template(
        "recharge/enter_number.html",
        initial_phone=initial_phone,
        country_iso=detect_country_iso_from_phone(initial_phone) or "AF",
    )


@recharge_bp.post("/enter-number")
def enter_number_post():
    raw = request.form.get("phone", "")
    phone = normalize_phone_e164_light(raw)
    if not phone or not is_phone_length_valid(phone):
        # Re-render with error flag (no text hardcoded; template uses i18n)
        return render_template(
            "recharge/enter_number.html",
            initial_phone=phone or "+93",
            country_iso=detect_country_iso_from_phone(phone) or "AF",
            phone_error=True,
        ), 400

    session["recharge_phone"] = phone
    return redirect(url_for("recharge.select_amount_get"))


# ---------------------------
# Select amount
# ---------------------------
@recharge_bp.get("/select-amount")
def select_amount_get():
    phone = session.get("recharge_phone")
    if not phone:
        return redirect(url_for("recharge.enter_number_get"))

    country_iso = detect_country_iso_from_phone(phone) or "FR"

    # Reloadly auto detect + amounts
    operator = get_reloadly_operator_auto_detect(phone=phone, country_iso=country_iso)
    operator_amounts = None
    if operator.get("id"):
        operator_amounts = get_reloadly_operator_amounts(operator_id=operator["id"])

    ctx = {
        "phone": phone,
        "country_iso": country_iso,
        "operator": operator,
        "amounts": operator_amounts or {},
        "tax_rate": 0.10,
    }
    return render_template("recharge/select_amount.html", **ctx)


# ---------------------------
# AJAX: quote conversion (debounced)
# ---------------------------
@recharge_bp.post("/api/quote")
def api_quote():
    phone = session.get("recharge_phone")
    if not phone:
        return jsonify({"ok": False}), 401

    operator_id = request.json.get("operatorId")
    amount = request.json.get("amount")

    try:
        operator_id = int(operator_id)
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False}), 400

    q = quote_local_amount(operator_id=operator_id, amount=amount)
    return jsonify({"ok": True, **q})


# ---------------------------
# AJAX: change operator (optional)
# ---------------------------
@recharge_bp.post("/api/operator")
def api_set_operator():
    phone = session.get("recharge_phone")
    if not phone:
        return jsonify({"ok": False}), 401

    operator_id = request.json.get("operatorId")
    try:
        operator_id = int(operator_id)
    except Exception:
        return jsonify({"ok": False}), 400

    amounts = get_reloadly_operator_amounts(operator_id=operator_id)
    return jsonify({"ok": True, "amounts": amounts})

@recharge_bp.post("/api/store-total")
def api_store_total():
    total = request.json.get("total")
    try:
        float(total)
    except Exception:
        return jsonify({"ok": False}), 400

    session["recharge_total_amount"] = str(total)
    return jsonify({"ok": True})