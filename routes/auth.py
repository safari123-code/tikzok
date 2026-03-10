# ---------------------------
# Auth Routes — FINAL CLEAN
# ---------------------------

from flask import Blueprint, render_template, request, session, redirect, url_for
import re
import time

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------------------
# CONFIG OTP
# ---------------------------
OTP_EXPIRATION_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN = 30


# ---------------------------
# Helpers
# ---------------------------
def _valid_email(email: str):
    """
    Robust email validation.
    Accepts common formats:
    user@gmail.com
    user.name@gmail.com
    user+alias@gmail.com
    """

    if not email:
        return False

    email = email.strip().lower()

    pattern = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"

    return re.match(pattern, email) is not None


def _mask_phone(phone: str) -> str:
    if not phone:
        return ""
    p = phone.strip()
    if len(p) <= 4:
        return "****"
    return f"{p[:3]} **** {p[-2:]}"


# ============================================================
# LOGIN (EMAIL)
# ============================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        email_value = (request.form.get("email") or "").strip().lower()

        if not _valid_email(email_value):
            return render_template("auth/email_login.html", error=True)

        if name:
            session["user_name"] = name

        # Cooldown protection
        last_sent = session.get("email_last_sent")
        if last_sent and time.time() - last_sent < OTP_RESEND_COOLDOWN:
            return render_template("auth/email_login.html", error=True)

        try:

            from services.email_otp_service import EmailOTPService

            code = EmailOTPService.send_verification(email_value)

        except Exception as e:

            print("EMAIL ERROR:", e)
            return render_template("auth/email_login.html", error=True)

        # Save OTP session
        session["pending_email"] = email_value
        session["email_code"] = code
        session["email_expires"] = time.time() + OTP_EXPIRATION_SECONDS
        session["email_attempts"] = 0
        session["email_last_sent"] = time.time()

        return redirect(url_for("auth.email_code"))

    return render_template("auth/email_login.html")


# ============================================================
# EMAIL OTP VERIFY
# ============================================================
@auth_bp.route("/email-code", methods=["GET", "POST"])
def email_code():

    email_value = session.get("pending_email")
    saved_code = session.get("email_code")
    expires = session.get("email_expires")
    attempts = session.get("email_attempts", 0)

    if not email_value:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        entered_code = (request.form.get("code") or "").strip()

        # Expired OTP
        if not expires or time.time() > expires:
            session.clear()
            return redirect(url_for("auth.login"))

        # Too many attempts
        if attempts >= OTP_MAX_ATTEMPTS:
            session.clear()
            return redirect(url_for("auth.login"))

        # Wrong code
        if entered_code != saved_code:
            session["email_attempts"] = attempts + 1
            return render_template(
                "auth/email_code.html",
                email=email_value,
                error=True
            )

        # SUCCESS LOGIN
        session["user_id"] = 1
        session["user_email"] = email_value

        session.pop("pending_email", None)
        session.pop("email_code", None)
        session.pop("email_expires", None)
        session.pop("email_attempts", None)
        session.pop("email_last_sent", None)

        return redirect("/")

    return render_template("auth/email_code.html", email=email_value)


# ============================================================
# PHONE LOGIN
# ============================================================
@auth_bp.route("/phone", methods=["GET", "POST"])
def phone():

    if request.method == "POST":

        name = (request.form.get("name") or "").strip()
        local_number = request.form.get("phone")
        country_code = request.form.get("country_code")

        if not local_number:
            return render_template("auth/phone_login.html", error=True)

        phone_number = f"{country_code}{local_number}".replace(" ", "")

        if name:
            session["user_name"] = name

        session["pending_phone"] = phone_number

        return redirect(url_for("auth.otp"))

    return render_template("auth/phone_login.html")


# ============================================================
# PHONE OTP
# ============================================================
@auth_bp.route("/otp", methods=["GET", "POST"])
def otp():

    phone_value = session.get("pending_phone")

    if not phone_value:
        return redirect(url_for("auth.phone"))

    if request.method == "POST":

        session["user_id"] = 1
        session["user_phone"] = phone_value

        session.pop("pending_phone", None)

        return redirect("/")

    masked_phone = _mask_phone(phone_value)

    return render_template(
        "auth/otp.html",
        phone=phone_value,
        masked_phone=masked_phone
    )


# ============================================================
# LOGOUT
# ============================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ============================================================
# LOGOUT CONFIRM
# ============================================================
@auth_bp.route("/logout-confirm")
def logout_confirm():

    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    return render_template("auth/logout_confirm.html")