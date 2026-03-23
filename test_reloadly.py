import requests
from config import RELOADLY_AUTH_URL, RELOADLY_BASE_URL
import os

# ---------------------------
# GET TOKEN
# ---------------------------
res = requests.post(RELOADLY_AUTH_URL, json={
    "client_id": os.getenv("RELOADLY_CLIENT_ID"),
    "client_secret": os.getenv("RELOADLY_CLIENT_SECRET"),
    "grant_type": "client_credentials",
    "audience": RELOADLY_BASE_URL
})

data = res.json()
token = data.get("access_token")

print("TOKEN:", token[:20] if token else "ERROR")

# ---------------------------
# TEST OPERATORS
# ---------------------------
url = f"{RELOADLY_BASE_URL}/operators/countries/FR"

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/com.reloadly.topups-v1+json"
}

res = requests.get(url, headers=headers)

print("STATUS:", res.status_code)
print("DATA:", res.text[:300])