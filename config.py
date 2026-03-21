# ---------------------------
# config.py
# ---------------------------

import os

# ---------------------------
# Optional dotenv (local dev)
# ---------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---------------------------
# Environment
# ---------------------------

ENV = os.getenv("ENV", "development")
IS_PROD = ENV == "production"

# ---------------------------
# Flask
# ---------------------------

SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(32)

SESSION_COOKIE_SECURE = IS_PROD
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ---------------------------
# Database
# ---------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# ---------------------------
# Reloadly API
# ---------------------------

RELOADLY_CLIENT_ID = os.getenv("RELOADLY_CLIENT_ID", "")
RELOADLY_CLIENT_SECRET = os.getenv("RELOADLY_CLIENT_SECRET", "")

# 🔥 FIX IMPORTANT
RELOADLY_ENV = os.getenv("RELOADLY_ENV", "SANDBOX").upper()

# ---------------------------
# Telnyx SMS OTP
# ---------------------------

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_SMS_FROM = os.getenv("TELNYX_SMS_FROM", "")

# ---------------------------
# Amazon SES
# ---------------------------

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")

# ---------------------------
# Stripe
# ---------------------------

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

STRIPE_MODE = "live" if STRIPE_SECRET_KEY.startswith("sk_live") else "test"

if not STRIPE_WEBHOOK_SECRET:
    print("⚠️ WARNING: STRIPE_WEBHOOK_SECRET is missing")

# ---------------------------
# Payment settings
# ---------------------------

CURRENCY = os.getenv("CURRENCY", "eur")

# ---------------------------
# Admin (FINAL CLEAN)
# ---------------------------

ADMIN_EMAILS_ENV = {
    email.strip().lower()
    for email in os.getenv("ADMIN_EMAILS", "").split(",")
    if email.strip()
}

ADMIN_EMAILS_STATIC = {
    "info@tikzok.com",
    "safarigulahmad616@gmail.com",
    "admin3@email.com"
}

ADMIN_EMAILS = ADMIN_EMAILS_ENV.union(ADMIN_EMAILS_STATIC)

SUPER_ADMIN_EMAIL = "info@tikzok.com"

# ---------------------------
# App
# ---------------------------

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# ---------------------------
# Security
# ---------------------------

MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

# ---------------------------
# Debug (temp)
# ---------------------------

print("ENV:", ENV)
print("RELOADLY ENV:", RELOADLY_ENV)
print("STRIPE MODE:", STRIPE_MODE)