# ---------------------------
# Reloadly Phone Lookup
# ---------------------------

import requests
from services.reloadly_auth import get_reloadly_token


def lookup_phone_number(phone, country):

    token = get_reloadly_token()

    if not token:
        return None

    url = f"https://topups.reloadly.com/operators/auto-detect/phone/{phone}/countries/{country}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:

        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            print("Reloadly error:", res.text)
            return None

        data = res.json()

        logos = data.get("logoUrls") or []

        logo = None
        if logos:
            logo = logos[0]["url"] if isinstance(logos[0], dict) else logos[0]

        return {
            "id": data.get("operatorId"),
            "name": data.get("name"),
            "logo_url": logo,
            "country": (data.get("country") or {}).get("name"),
            "country_iso": (data.get("country") or {}).get("isoName")
        }

    except Exception as e:
        print("Reloadly lookup error:", e)
        return None