from flask import Blueprint, render_template, request, redirect, url_for, session

from services.payment_service import (
    get_points_balance,
    compute_points_usage,
    create_checkout,
    get_checkout,
)

payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


# ---------------------------
# Payment method GET
# ---------------------------
@payment_bp.get("/method")
def method_get():
    phone = session.get("recharge_phone", "")
    amount = session.get("recharge_total_amount", "0.00")

    points = get_points_balance()

    return render_template(
        "payment/payment_method.html",
        phone=phone,
        amount=amount,
        points=points,
        is_forfait_minutes=False,
    )


# ---------------------------
# Payment method POST
# ---------------------------
@payment_bp.post("/method")
def method_post():
    selected_method = request.form.get("method", "card")
    save_card = request.form.get("save_card") == "1"
    use_points = request.form.get("use_points") == "1"

    phone = session.get("recharge_phone", "")
    amount = session.get("recharge_total_amount", "0.00")

    points_used, final_amount = compute_points_usage(
        amount=amount,
        use_points=use_points,
    )

    checkout = create_checkout(
        phone=phone,
        amount=amount,
        final_amount=final_amount,
        points_used=points_used,
        method=selected_method,
        save_card=save_card,
    )

    session["checkout_id"] = checkout["id"]

    return redirect(url_for("payment.success_get"))


# ---------------------------
# Payment success
# ---------------------------
@payment_bp.get("/success")
def success_get():
    checkout_id = session.get("checkout_id")
    checkout = get_checkout(checkout_id)

    if not checkout:
        return redirect(url_for("payment.method_get"))

    return render_template(
        "payment/payment_success.html",
        checkout=checkout,
    )