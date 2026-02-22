# ---------------------------
# Auth Routes — FINAL
# ---------------------------

from flask import Blueprint, render_template, request, session, redirect, url_for
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _valid_email(email: str):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or "")


# ENTRY (choix)
@auth_bp.route("/login")
def login():
    return render_template("auth/entry.html")


# EMAIL PAGE
@auth_bp.route("/email-page")
def email_page():
    return render_template("auth/email.html")


# EMAIL SUBMIT
@auth_bp.route("/email", methods=["POST"])
def email_submit():
    email = request.form.get("email")

    if not _valid_email(email):
        return render_template("auth/email.html", error=True)

    session["pending_email"] = email
    return redirect(url_for("auth.email_code"))


# EMAIL CODE
@auth_bp.route("/email-code", methods=["GET","POST"])
def email_code():
    email = session.get("pending_email")

    if not email:
        return redirect(url_for("auth.entry"))

    if request.method == "POST":
        session["user_id"] = 1
        session["user_name"] = email
        session.pop("pending_email", None)
        return redirect("/")

    return render_template("auth/email_code.html", email=email)


# PHONE PAGE
@auth_bp.route("/phone", methods=["GET","POST"])
def phone():

    if request.method == "POST":
        phone = request.form.get("phone")

        if not phone:
            return render_template("auth/phone.html", error=True)

        session["pending_phone"] = phone
        return redirect(url_for("auth.otp"))

    return render_template("auth/phone.html")


# OTP PAGE
@auth_bp.route("/otp", methods=["GET","POST"])
def otp():
    phone = session.get("pending_phone")

    if not phone:
        return redirect(url_for("auth.phone"))

    if request.method == "POST":
        session["user_id"] = 1
        session["user_name"] = phone
        session.pop("pending_phone", None)
        return redirect("/")

    return render_template("auth/otp.html", phone=phone)


# LOGOUT
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")