# ---------------------------
# Test Telnyx SMS
# ---------------------------

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TELNYX_API_KEY")

url = "https://api.telnyx.com/v2/messages"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "from": os.getenv("TELNYX_SMS_FROM"),
    "to": "+33758010217",   # ton numéro
    "text": "Test SMS Tikzok OTP"
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.text)