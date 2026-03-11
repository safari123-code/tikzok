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
# Amazon SES
# ---------------------------
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SES_FROM_EMAIL = os.getenv("SES_FROM_EMAIL")