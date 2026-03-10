# ---------------------------
# config.py
# ---------------------------

import os
from dotenv import load_dotenv

# Charger .env
load_dotenv()


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
# Reloadly API
# ---------------------------
RELOADLY_CLIENT_ID = os.getenv("RELOADLY_CLIENT_ID")
RELOADLY_CLIENT_SECRET = os.getenv("RELOADLY_CLIENT_SECRET")
RELOADLY_ENV = os.getenv("RELOADLY_ENV", "sandbox")


# ---------------------------
# Telnyx SMS OTP
# ---------------------------
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
TELNYX_SMS_FROM = os.getenv("TELNYX_SMS_FROM")


# ---------------------------
# Amazon SES
# ---------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")


# ---------------------------
# Stripe
# ---------------------------
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")