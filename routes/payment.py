# ---------------------------
# routes/payment.py
# ---------------------------

import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.points_service import PointsService
from services.history_service import HistoryService
from services.idempotency_service import IdempotencyService
from services.order_service import OrderService
from services.email_service import EmailService
from services.stripe_service import StripeService
import services.reloadly_service as ReloadlyService

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


# ---------------------------
# Helpers
# ---------------------------
def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _get_payment_context():
    phone = session.get("recharge_phone", "")
    recharge_amount = _safe_float(session.get("recharge_total_amount"), 0.0)

    points_available = _safe_float(PointsService.get_points(), 0.0)
    use_points = bool(session.get("payment_use_points", False))

    points_used = min(points_available, recharge_amount) if use_points else 0.0
    final_amount = max(0.0, recharge_amount - points_used)

    return {
        "phone": phone,
        "recharge_amount": recharge_amount,
        "points_available": points_available,
        "use_points": use_points,
        "points_used": points_used,
        "final_amount": final_amount,
    }


def _build_checkout_metadata(idem_key: str):
    ctx = _get_payment_context()

    return {
        "payment_idempotency_key": idem_key,
        "recharge_phone": str(ctx["phone"] or ""),
        "recharge_amount": f"{ctx['recharge_amount']:.2f}",
        "charged_amount": f"{ctx['final_amount']:.2f}",
        "points_used": f"{ctx['points_used']:.2f}",
        "country_iso": str(session.get("country_iso") or ""),
        "user_id": str(session.get("user_id") or ""),
        "user_email": str(session.get("user_email") or session.get("pending_email") or ""),
    }


# ---------------------------
# Payment method
# ---------------------------
@payment_bp.get("/method")
def method_get():

    ctx = _get_payment_context()

    if not ctx["recharge_amount"]:
        return redirect(url_for("recharge.select_amount_get"))

    return render_template(
        "payment/method.html",
        phone=ctx["phone"],
        amount=ctx["recharge_amount"],
        points_available=ctx["points_available"],
        use_points=ctx["use_points"],
        points_used=ctx["points_used"],
        final_amount=ctx["final_amount"],
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

    ctx = _get_payment_context()

    if not ctx["recharge_amount"]:
        return redirect(url_for("recharge.select_amount_get"))

    if not session.get("payment_idempotency_key"):
        session["payment_idempotency_key"] = str(uuid.uuid4())

    return render_template(
        "payment/card.html",
        phone=ctx["phone"],
        amount=ctx["recharge_amount"],
        final_amount=ctx["final_amount"],
        points_used=ctx["points_used"],
        save_card=session.get("payment_save_card", True),
    )


# ---------------------------
# Process card payment
# ---------------------------
@payment_bp.post("/card")
def card_post():

    if session.get("payment_selected_method") != "card":
        return redirect(url_for("payment.method_get"))

    ctx = _get_payment_context()

    if not ctx["recharge_amount"]:
        return redirect(url_for("recharge.select_amount_get"))

    idem_key = session.get("payment_idempotency_key")
    if not idem_key:
        idem_key = str(uuid.uuid4())
        session["payment_idempotency_key"] = idem_key

    existing = IdempotencyService.get_result(idem_key)
    if existing:
        session["payment_success_payload"] = existing
        return jsonify({"success": True})

    metadata = _build_checkout_metadata(idem_key)

    try:
        intent = StripeService.create_payment_intent(
            amount=ctx["final_amount"],
            currency="eur",
            metadata=metadata
        )

        return jsonify({
            "client_secret": intent.client_secret
        })

    except Exception as e:
        print("Stripe payment intent error:", e)

        return jsonify({
            "error": "payment_error"
        }), 400


# ---------------------------
# Stripe webhook
# ---------------------------
@payment_bp.post("/webhook")
def stripe_webhook_post():

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    # ---------------------------
    # Stripe signature (SECURE)
    # ---------------------------
    try:
        event = StripeService.construct_webhook_event(payload, sig_header)
    except Exception as e:
        print("❌ Stripe webhook signature error:", e)
        return jsonify({"ok": False}), 400

    event_type = event.get("type")
    event_data = (event.get("data") or {}).get("object") or {}

    print("✅ Stripe webhook event:", event_type)

    # ---------------------------
    # Payment succeeded
    # ---------------------------
    if event_type == "payment_intent.succeeded":

        metadata = event_data.get("metadata", {}) or {}
        idem_key = metadata.get("payment_idempotency_key")

        print("📦 Metadata:", metadata)

        # ---------------------------
        # Idempotency protection
        # ---------------------------
        if idem_key and IdempotencyService.get_result(idem_key):
            print("⚠️ Duplicate webhook ignored:", idem_key)
            return jsonify({"ok": True, "deduplicated": True}), 200

        try:
            # ---------------------------
            # Extract & validate
            # ---------------------------
            phone = str(metadata.get("recharge_phone") or "").strip()
            amount = _safe_float(metadata.get("recharge_amount"), 0.0)

            if not phone or amount <= 0:
                print("❌ Invalid webhook data:", phone, amount)
                return jsonify({"ok": False}), 400

            print("🚀 Sending recharge:", phone, amount)

            # ---------------------------
            # Reloadly call (FIX BUG)
            # ---------------------------
            reloadly_result = ReloadlyService.send_topup(
                phone=phone,
                amount=amount
            )

            print("✅ Reloadly success:", reloadly_result)

            # ---------------------------
            # Build success payload
            # ---------------------------
            payload_obj = OrderService.build_success_payload(
                amount=amount
            )

            if idem_key:
                IdempotencyService.store_result(idem_key, payload_obj)

            # ---------------------------
            # Email confirmation
            # ---------------------------
            user_email = metadata.get("user_email")

            if user_email:
                try:
                    EmailService.send_payment_success(
                        email=user_email,
                        payload=payload_obj,
                        phone=phone,
                    )
                except Exception as email_error:
                    print("⚠️ Email error:", email_error)

        except Exception as process_error:
            print("❌ Webhook processing error:", process_error)
            return jsonify({"ok": False}), 500

    # ---------------------------
    # Always return OK to Stripe
    # ---------------------------
    return jsonify({"ok": True}), 200


# ---------------------------
# Payment success page
# ---------------------------
@payment_bp.get("/success")
def success_get():

    payload = session.get("payment_success_payload")

    # Si webhook déjà passé
    if payload:
        return render_template(
            "payment/success.html",
            amount=payload["amount"],
            order_number=payload["orderNumber"],
            reference=payload["reference"],
            date=payload["date"],
        )

    # Sinon fallback : récupérer PaymentIntent
    payment_intent_id = request.args.get("payment_intent")

    if payment_intent_id:

        try:
            intent = StripeService.retrieve_payment(payment_intent_id)

            if intent.status == "succeeded":

                payload = OrderService.build_success_payload(
                    amount=intent.metadata.get("recharge_amount")
                )

                session["payment_success_payload"] = payload

                return render_template(
                    "payment/success.html",
                    amount=payload["amount"],
                    order_number=payload["orderNumber"],
                    reference=payload["reference"],
                    date=payload["date"],
                )

        except Exception as e:
            print("Stripe success retrieve error:", e)

    return redirect(url_for("payment.method_get"))


# ---------------------------
# Finish success flow
# ---------------------------
@payment_bp.post("/success/finish")
def success_finish_post():

    payload = session.get("payment_success_payload")

    if payload:
        phone = (session.get("recharge_phone") or "").replace(" ", "")

        if phone:
            country = session.get("country_iso") or phone[:3]

            HistoryService.add(
                phone=phone,
                amount=str(payload["amount"]),
                country=country
            )

        PointsService.refresh()

    # ---------------------------
    # Clean session
    # ---------------------------
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