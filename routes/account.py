# ---------------------------
# Account routes — FINAL
# ---------------------------

import os
from flask import Blueprint, render_template, session, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from services.order_service import OrderService

account_bp = Blueprint("account", __name__, url_prefix="/account")


# ---------------------------
# About page
# ---------------------------
@account_bp.route("/about")
def about():
    return render_template("account/about.html")


# ---------------------------
# Payment methods page
# ---------------------------
@account_bp.route("/payment-methods")
def payment_methods():

    cards = OrderService.get_saved_cards()

    return render_template(
        "account/card_storage.html",
        cards=cards
    )

# ---------------------------
# Profile page
# ---------------------------
@account_bp.route("/profile", methods=["GET", "POST"])
def profile():

    # =========================
    # SAVE
    # =========================
    if request.method == "POST":

        # ---- TEXT FIELDS ----
        name = (request.form.get("name") or "").strip()
        birthdate = request.form.get("birthdate") or ""

        if name:
            session["user_name"] = name

        if birthdate:
            session["user_birthdate"] = birthdate

        # ---- AVATAR UPLOAD ----
        file = request.files.get("avatar")

        if file and file.filename:

            filename = secure_filename(file.filename)

            upload_folder = os.path.join(
                current_app.static_folder,
                "uploads",
                "avatars"
            )

            os.makedirs(upload_folder, exist_ok=True)

            path = os.path.join(upload_folder, filename)

            file.save(path)

            session["user_avatar"] = f"/static/uploads/avatars/{filename}"

        return redirect(url_for("account.profile"))

    # =========================
    # READ
    # =========================
    user = {
        "name": session.get("user_name", "Utilisateur"),
        "email": session.get("user_email", ""),
        "phone": session.get("user_phone", ""),
        "birthdate": session.get("user_birthdate", ""),
        "avatar": session.get("user_avatar"),
    }

    return render_template(
        "account/profile.html",
        user=user
    )