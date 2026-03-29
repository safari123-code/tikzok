# ---------------------------
# routes/payment.py
# ---------------------------

import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from services.order.points_service import PointsService
from services.order.history_service import HistoryService
from services.core.idempotency_service import IdempotencyService
from services.order.order_service import OrderService
from services.communication.email_service import EmailService
from services.stripe.stripe_service import StripeService
from services.payment.fees_service import FeesService

# ---------------------------
# Reloadly Services (NEW CLEAN ARCH)
# ---------------------------
from services.reloadly.airtime_service import send_topup, get_topup_status
from services.reloadly.data_service import send_data_topup

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

    base_amount = _safe_float(session.get("recharge_amount"), 0.0)
    recharge_total_amount = _safe_float(session.get("recharge_total_amount"), 0.0)

    points_available = _safe_float(PointsService.get_points(), 0.0)
    use_points = bool(session.get("payment_use_points", False))

    points_used = min(points_available, recharge_total_amount) if use_points else 0.0
    final_amount = max(0.0, recharge_total_amount - points_used)

    return {
        "phone": phone,
        "base_amount": base_amount,
        "recharge_amount": recharge_total_amount,
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
        "base_amount": f"{ctx['base_amount']:.2f}",
        "recharge_amount": f"{ctx['recharge_amount']:.2f}",
        "charged_amount": f"{ctx['final_amount']:.2f}",
        "points_used": f"{ctx['points_used']:.2f}",
        "country_iso": str(session.get("country_iso") or ""),
        "user_id": str(session.get("user_id") or ""),
        "user_email": str(session.get("user_email") or session.get("pending_email") or ""),
        "forfait_id": str(session.get("recharge_forfait", {}).get("id") or "")
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
# Card page
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
# Stripe webhook (FINAL SAFE PRODUCTION)
# ---------------------------
@payment_bp.post("/webhook")
def stripe_webhook_post():

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = StripeService.construct_webhook_event(payload, sig_header)
    except Exception as e:
        print("❌ Stripe webhook signature error:", e)
        return jsonify({"ok": False}), 400

    event_type = event.get("type")
    event_data = (event.get("data") or {}).get("object") or {}

    print("✅ Stripe webhook event:", event_type)

    if event_type != "payment_intent.succeeded":
        return jsonify({"ok": True}), 200

    metadata = event_data.get("metadata", {}) or {}
    idem_key = str(metadata.get("payment_idempotency_key") or "").strip()

    print("📦 Metadata:", metadata)

    if not idem_key:
        print("❌ Missing idempotency key")
        return jsonify({"ok": False}), 400

    existing = IdempotencyService.get_result(idem_key)
    if existing:
        print("⚠️ Duplicate webhook ignored:", idem_key)
        return jsonify({"ok": True, "deduplicated": True}), 200

    try:
        # ---------------------------
        # Validation Stripe
        # ---------------------------
        stripe_status = str(event_data.get("status") or "").strip()
        if stripe_status != "succeeded":
            return jsonify({"ok": True}), 200

        phone = str(metadata.get("recharge_phone") or "").strip()
        country_iso = str(metadata.get("country_iso") or "").strip()
        forfait_id = str(metadata.get("forfait_id") or "").strip()
        user_email = str(metadata.get("user_email") or "").strip()

        base_amount = _safe_float(metadata.get("base_amount"), 0.0)
        charged_amount = _safe_float(metadata.get("charged_amount"), 0.0)
        points_used = _safe_float(metadata.get("points_used"), 0.0)

        if not phone or base_amount <= 0:
            print("❌ Invalid metadata payload")
            return jsonify({"ok": False}), 400

        stripe_amount_received = _safe_float(event_data.get("amount_received"), 0) / 100.0
        stripe_currency = str(event_data.get("currency") or "").lower()

        if stripe_currency != "eur":
            print("❌ Unexpected Stripe currency:", stripe_currency)
            return jsonify({"ok": False}), 400

        if abs(stripe_amount_received - charged_amount) > 0.01:
            print("❌ Amount mismatch")
            return jsonify({"ok": False}), 400

        # ---------------------------
        # Recharge logic
        # ---------------------------
        payout_amount = round(base_amount, 2)

        print("🚀 SENDING TOPUP:", phone, payout_amount)

        try:
            if forfait_id:
                reloadly_result = send_data_topup(
                    phone=phone,
                    plan_id=int(forfait_id),
                    country_iso=country_iso
                )
            else:
                reloadly_result = send_topup(
                    phone=phone,
                    amount=payout_amount,
                    country_iso=country_iso
                )

        except Exception as reloadly_error:
            print("❌ Reloadly error:", reloadly_error)

            IdempotencyService.store_result(idem_key, {
                "status": "FAILED",
                "reason": "reloadly_error"
            })

            return jsonify({"ok": True}), 200

        transaction_id = reloadly_result.get("transaction_id")

        if not transaction_id:
            print("❌ Missing Reloadly transaction_id")

            IdempotencyService.store_result(idem_key, {
                "status": "FAILED",
                "reason": "no_transaction_id"
            })

            return jsonify({"ok": True}), 200

        # ---------------------------
        # Success payload
        # ---------------------------
        payload_obj = OrderService.build_success_payload(amount=base_amount)
        payload_obj.update({
            "transaction_id": transaction_id,
            "charged_amount": charged_amount,
            "points_used": points_used
        })

        # ---------------------------
        # Store idempotent result
        # ---------------------------
        IdempotencyService.store_result(idem_key, payload_obj)
        IdempotencyService.store_result(idem_key, payload_obj)
        # ---------------------------
        # Optional email
        # ---------------------------
        if user_email:
            try:
                EmailService.send_payment_success(
                    email=user_email,
                    payload=payload_obj,
                    phone=phone,
                )
            except Exception as email_error:
                print("❌ Email error:", email_error)

    except Exception as process_error:
        print("❌ Webhook processing error:", process_error)
        return jsonify({"ok": True}), 200

    return jsonify({"ok": True}), 200



# ---------------------------
# Payment status (FIX IMPORTANT)
# ---------------------------
@payment_bp.get("/status")
def payment_status():

    payload = session.get("payment_success_payload")

    if not payload:
        return jsonify({"status": "pending"})

    transaction_id = payload.get("transaction_id")

    if transaction_id:
        try:
            result = get_topup_status(transaction_id)
            status = result.get("status")

            if status == "SUCCESSFUL":
                return jsonify({"status": "success"})
            if status == "FAILED":
                return jsonify({"status": "failed"})

            return jsonify({"status": "processing"})

        except Exception as e:
            print("Status check error:", e)
            return jsonify({"status": "processing"})

    return jsonify({"status": "processing"})

# ---------------------------
# Payment success page (FINAL PRO SAFE)
# ---------------------------
@payment_bp.get("/success")
def payment_success():

    payload = session.get("payment_success_payload") or {}

    # ---------------------------
    # Processing state
    # ---------------------------
    if not payload:
        return render_template(
            "payment/success.html",
            status="processing",
            amount=None,
            date=None,
            order_number=None,
            reference=None
        )

    # ---------------------------
    # Safe payload mapping
    # ---------------------------
    return render_template(
        "payment/success.html",
        status="success",
        amount=payload.get("amount"),
        date=payload.get("date"),
        order_number=payload.get("order_number"),
        reference=payload.get("transaction_id")
    )