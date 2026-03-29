# ---------------------------
# Feature: Reloadly Operators List Service (DATA FILTERED)
# ---------------------------

from services.reloadly.auth_service import get_reloadly_token, _safe_request
from config import RELOADLY_BASE_URL


def get_reloadly_operators(page: int = 1, size: int = 50, data_only: bool = False):

    token = get_reloadly_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    url = (
        f"{RELOADLY_BASE_URL}/operators"
        f"?includeBundles=true"
        f"&includeData=true"
        f"&page={page}"
        f"&size={size}"
    )

    try:
        res = _safe_request("GET", url, headers=headers)

        if res.status_code != 200:
            print("❌ Operators list error:", res.text)
            return []

        data = res.json()

        operators = []

        for op in data.get("content", []):

            supports_data = bool(op.get("data"))
            supports_bundle = bool(op.get("bundle"))

            # 🔥 FILTRE DATA UNIQUEMENT
            if data_only and not supports_data:
                continue

            operators.append({
                "id": op.get("id"),
                "name": op.get("name"),
                "country": (op.get("country") or {}).get("isoName"),
                "logo": (op.get("logoUrls") or [None])[0],  # FIX logo
                "supports_data": supports_data,
                "supports_bundle": supports_bundle,
                "currency": (
                    op.get("localCurrency")
                    or (op.get("fx") or {}).get("currencyCode")
                ),
                "min_amount": op.get("minAmount"),
                "max_amount": op.get("maxAmount"),
            })

        print(f"✅ OPERATORS FETCHED: {len(operators)}")

        return operators

    except Exception as e:
        print("❌ Operators list exception:", e)
        return []