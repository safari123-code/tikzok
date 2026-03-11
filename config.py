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
# Flask
# ---------------------------

SECRET_KEY = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV", "development")

# ---------------------------
# Database
# ---------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# ---------------------------
# Reloadly API (optional)
# ---------------------------

RELOADLY_CLIENT_ID = os.getenv("RELOADLY_CLIENT_ID", "")
RELOADLY_CLIENT_SECRET = os.getenv("RELOADLY_CLIENT_SECRET", "")
RELOADLY_ENV = os.getenv("RELOADLY_ENV", "sandbox")

# ---------------------------
# Telnyx SMS OTP (optional)
# ---------------------------

TELNYX_API_KEY = os.getenv("TELNYX_API_KEY", "")
TELNYX_SMS_FROM = os.getenv("TELNYX_SMS_FROM", "")

# ---------------------------
# Amazon SES (active)
# ---------------------------

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")

# ---------------------------
# Stripe (optional)
# ---------------------------

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")