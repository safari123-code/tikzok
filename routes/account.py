# ---------------------------
# Account routes — FINAL PRO
# ---------------------------

import os
from flask import Blueprint, render_template, session, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

from services.order.order_service import OrderService
from services.user.user_service import UserService

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

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("auth.login"))

    # =========================
    # SAVE
    # =========================
    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        birthdate = request.form.get("birthdate") or ""

        # ---- UPDATE USER (DB JSON) ----
        UserService.update(
            user_id=user_id,
            name=name
        )

        # ---- UPDATE SESSION (UI instant) ----
        if name:
            session["user_name"] = name

        if birthdate:
            session["user_birthdate"] = birthdate

        # ---- AVATAR ----
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

            avatar_url = f"/static/uploads/avatars/{filename}"

            session["user_avatar"] = avatar_url

            # Optionnel : sauvegarder aussi en user
            UserService.update_avatar(user_id, avatar_url)

        return redirect(url_for("account.profile"))

    # =========================
    # READ (IMPORTANT)
    # =========================
    user_data = UserService.get_by_id(user_id) or {}

    user = {
        "name": user_data.get("name") or session.get("user_name", "Utilisateur"),
        "email": user_data.get("email") or session.get("user_email", ""),
        "phone": user_data.get("phone") or session.get("user_phone", ""),
        "birthdate": session.get("user_birthdate", ""),
        "avatar": session.get("user_avatar"),
    }

    return render_template(
        "account/profile.html",
        user=user
    )