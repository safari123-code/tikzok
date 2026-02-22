# ---------------------------
# Account routes
# ---------------------------

from flask import Blueprint, render_template

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/about")
def about():
    return render_template("account/about.html")

# ---------------------------
# Payment methods page
# ---------------------------

@account_bp.route("/payment-methods")
def payment_methods():
    cards = []  # plus tard DB
    return render_template(
        "account/payment_methods.html",
        cards=cards
    )