# ---------------------------
# routes/payment.py
# ---------------------------

import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session

from services.points_service import PointsService
from services.history_service import HistoryService
from services.card_validator import CardValidator
from services.idempotency_service import IdempotencyService
from services.order_service import OrderService
from services.email_service import EmailService

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


# ---------------------------
# Payment method
# ---------------------------
@payment_bp.get("/method")
def method_get():

    phone = session.get("recharge_phone", "")
    amount = session.get("recharge_total_amount")

    if not amount:
        return redirect(url_for("recharge.select_amount_get"))

    amount_value = float(amount)

    points_available = PointsService.get_points()

    use_points = bool(session.get("payment_use_points", False))

    points_used = min(points_available, amount_value) if use_points else 0.0

    final_amount = max(0.0, amount_value - points_used)

    return render_template(
        "payment/method.html",
        phone=phone,
        amount=amount_value,
        points_available=points_available,
        use_points=use_points,
        points_used=points_used,
        final_amount=final_amount,
        selected_method=session.get("payment_selected_method", "card"),
        save_card=session.get("payment_save_card", True),
        is_forfait_minutes=False,
    )


@payment_bp.post("/method")
def method_post():

    selected_method = request.form.get("selected_method", "card")
    save_card = request.form.get("save_card") == "1"
    use_points = request.form.get("use_points") == "1"

    session["payment_selected_method"] = selected_method
    session["payment_save_card"] = save_card
    session["payment_use_points"] = use_points

    if selected_method != "card":
        session["payment_toast"] = "payment.methodUnavailable"
        return redirect(url_for("payment.method_get"))

    return redirect(url_for("payment.card_get"))


# ---------------------------
# Card payment page
# ---------------------------
@payment_bp.get("/card")
def card_get():

    if session.get("payment_selected_method") != "card":
        return redirect(url_for("payment.method_get"))

    phone = session.get("recharge_phone", "")
    amount = session.get("recharge_total_amount", "0")

    if not session.get("payment_idempotency_key"):
        session["payment_idempotency_key"] = str(uuid.uuid4())

    return render_template(
        "payment/card.html",
        phone=phone,
        amount=amount,
        save_card=session.get("payment_save_card", True),
    )


# ---------------------------
# Process card payment
# ---------------------------
@payment_bp.post("/card")
def card_post():

    idem_key = session.get("payment_idempotency_key")

    existing = IdempotencyService.get_result(idem_key)

    if existing:
        session["payment_success_payload"] = existing
        return redirect(url_for("payment.success_get"))

    name = request.form.get("card_name", "").strip()
    number = request.form.get("card_number", "").strip()
    expiry = request.form.get("card_expiry", "").strip()
    cvv = request.form.get("card_cvv", "").strip()

    save_card = request.form.get("save_card") == "1"

    errors = CardValidator.validate(name, number, expiry, cvv)

    if errors:

        return render_template(
            "payment/card.html",
            phone=session.get("recharge_phone", ""),
            amount=session.get("recharge_total_amount", "0"),
            save_card=save_card,
            form_error_keys=errors,
            card_name=name,
            card_number=CardValidator.mask_or_format(number),
            card_expiry=expiry,
        )

    payload = OrderService.build_success_payload(
        amount=session.get("recharge_total_amount", "0")
    )

    OrderService.maybe_store_card_tokenized(save_card, number, expiry)

    IdempotencyService.store_result(idem_key, payload)

    session["payment_success_payload"] = payload

    # ---------------------------
    # Send success email
    # ---------------------------
    user_email = session.get("user_email") or session.get("pending_email")

    if user_email:
        try:
            EmailService.send_payment_success(
                email=user_email,
                payload=payload,
                phone=session.get("recharge_phone")
            )
        except Exception as e:
            print("Email send error:", e)

    return redirect(url_for("payment.success_get"))


# ---------------------------
# Payment success page
# ---------------------------
@payment_bp.get("/success")
def success_get():

    payload = session.get("payment_success_payload")

    if not payload:
        return redirect(url_for("payment.method_get"))

    return render_template(
        "payment/success.html",
        amount=payload["amount"],
        order_number=payload["orderNumber"],
        reference=payload["reference"],
        date=payload["date"],
    )


# ---------------------------
# Finish success flow
# ---------------------------
@payment_bp.post("/success/finish")
def success_finish_post():

    payload = session.get("payment_success_payload")

    if payload:

        phone = (session.get("recharge_phone") or "").replace(" ", "")

        if phone:
            HistoryService.add(phone=phone, amount=str(payload["amount"]))

        PointsService.refresh()

    for k in [
        "payment_selected_method",
        "payment_use_points",
        "payment_save_card",
        "payment_success_payload",
        "payment_idempotency_key",
        "payment_toast",
    ]:
        session.pop(k, None)

    return redirect(url_for("recharge.enter_number_get"))


# ---------------------------
# Delete saved card
# ---------------------------
@payment_bp.post("/card/<card_id>/delete")
def delete_card_post(card_id):

    OrderService.delete_saved_card(
        user_id=session.get("user_id"),
        card_id=card_id
    )

    return redirect(url_for("account.payment_methods"))


# ---------------------------
# Set default card
# ---------------------------
@payment_bp.post("/card/<card_id>/default")
def set_default_card_post(card_id):

    OrderService.set_default_card(
        user_id=session.get("user_id"),
        card_id=card_id
    )

    return redirect(url_for("account.payment_methods"))


# ---------------------------
# Edit saved card
# ---------------------------
@payment_bp.route("/card/<card_id>/edit", methods=["GET", "POST"])
def edit_card_get(card_id):

    card = OrderService.get_saved_card(
        user_id=session.get("user_id"),
        card_id=card_id
    )

    if not card:
        return redirect(url_for("account.payment_methods"))

    if request.method == "POST":

        name = (request.form.get("card_name") or "").strip()
        number = (request.form.get("card_number") or "").strip()
        expiry = (request.form.get("card_expiry") or "").strip()

        OrderService.update_saved_card(
            card_id=card_id,
            name=name,
            number=number,
            expiry=expiry
        )

        return redirect(url_for("account.payment_methods"))

    return render_template(
        "account/edit_card.html",
        card=card
    )