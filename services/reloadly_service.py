# ---------------------------
# services/reloadly_service.py
# ---------------------------
import os
import requests

class ReloadlyService:
    @staticmethod
    def _token() -> str:
        # Ne jamais mettre en dur
        return os.environ.get("RELOADLY_ACCESS_TOKEN", "")

    @staticmethod
    def load_operator_and_amounts(phone: str, country_iso: str) -> dict:
        token = ReloadlyService._token()
        if not token:
            return {
                "operator_id": None,
                "operator_name": None,
                "operator_country": None,
                "operator_logo_url": None,
                "fixed_amounts": [],
                "min_amount": 2,
                "max_amount": 50,
            }

        phone_clean = phone.strip()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        # auto detect
        op_url = f"https://topups.reloadly.com/operators/auto-detect/phone/{phone_clean}/countries/{country_iso.upper()}"
        op_res = requests.get(op_url, headers=headers, timeout=15)
        if op_res.status_code != 200:
            return {
                "operator_id": None,
                "operator_name": None,
                "operator_country": None,
                "operator_logo_url": None,
                "fixed_amounts": [],
                "min_amount": 2,
                "max_amount": 50,
            }

        op = op_res.json()
        operator_id = op.get("id")
        operator_name = op.get("name")
        operator_country = (op.get("country") or {}).get("name")
        logos = op.get("logoUrls") or []
        operator_logo_url = logos[0] if logos else None

        fixed_amounts = []
        min_amount = None
        max_amount = None

        if operator_id:
            amt_url = f"https://topups.reloadly.com/operators/{operator_id}/amounts"
            amt_res = requests.get(amt_url, headers=headers, timeout=15)
            if amt_res.status_code == 200:
                amt = amt_res.json()
                fixed_amounts = [float(x) for x in (amt.get("fixedAmounts") or [])]
                min_amount = amt.get("minAmount")
                max_amount = amt.get("maxAmount")

        return {
            "operator_id": operator_id,
            "operator_name": operator_name,
            "operator_country": operator_country,
            "operator_logo_url": operator_logo_url,
            "fixed_amounts": fixed_amounts,
            "min_amount": float(min_amount) if min_amount is not None else 2.0,
            "max_amount": float(max_amount) if max_amount is not None else 50.0,
        }

    @staticmethod
    def quote(operator_id: int, amount: float) -> dict:
        # Ici on suppose un endpoint backend interne plus tard.
        # Pour l’instant, on renvoie un “shape” identique à Flutter.
        # Tu pourras remplacer sans toucher l’UI.
        # localAmount/localCurrency peuvent rester None si non dispo.
        return {"localAmount": None, "localCurrency": None}


# ---------------------------
# services/currency_service.py
# ---------------------------
class CurrencyService:
    _country_currency_by_prefix = {
        "+33": "EUR", "+44": "GBP", "+1": "USD", "+212": "MAD", "+225": "XOF", "+237": "XAF", "+234": "NGN",
        # ... (garde ta map complète si tu veux)
    }

    _fallback_rates = {
        "MAD": 10, "XOF": 650, "XAF": 650, "NGN": 1400,
        "USD": 1, "EUR": 1, "GBP": 1,
        # ... (garde ta map complète si tu veux)
    }

    @staticmethod
    def currency_from_phone(phone: str) -> str:
        for prefix, cur in CurrencyService._country_currency_by_prefix.items():
            if phone.startswith(prefix):
                return cur
        return "EUR"

    @staticmethod
    def received_display_value(phone: str, amount: float, selected_forfait: dict | None, quote: dict | None) -> str:
        # Forfait prioritaire
        if selected_forfait and selected_forfait.get("gb"):
            return str(selected_forfait["gb"])

        if quote and quote.get("localAmount") is not None and quote.get("localCurrency"):
            return f'{int(float(quote["localAmount"]))} {quote["localCurrency"]}'

        cur = CurrencyService.currency_from_phone(phone)
        rate = CurrencyService._fallback_rates.get(cur, 1)
        estimated = round(amount * rate)
        return f"{estimated} {cur}"


# ---------------------------
# services/points_service.py
# ---------------------------
class PointsService:
    @staticmethod
    def get_points() -> float:
        # Source backend (plus tard DB)
        return 0.0

    @staticmethod
    def refresh() -> None:
        return


# ---------------------------
# services/history_service.py
# ---------------------------
class HistoryService:
    @staticmethod
    def add(phone: str, amount: str) -> None:
        # Stockage DB plus tard
        return


# ---------------------------
# services/card_validator.py
# ---------------------------
import re
from datetime import datetime

class CardValidator:
    @staticmethod
    def _digits_only(s: str) -> str:
        return re.sub(r"[^0-9]", "", s or "")

    @staticmethod
    def luhn_check(digits: str) -> bool:
        total = 0
        alternate = False
        for ch in reversed(digits):
            n = int(ch)
            if alternate:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
            alternate = not alternate
        return total % 10 == 0

    @staticmethod
    def expiry_valid(mm_yy: str) -> bool:
        if not re.match(r"^(0[1-9]|1[0-2])/\d{2}$", mm_yy or ""):
            return False
        mm, yy = mm_yy.split("/")
        mm = int(mm)
        yy = int(yy)

        now = datetime.utcnow()
        current_year2 = now.year % 100
        current_month = now.month

        if yy > current_year2:
            return True
        if yy < current_year2:
            return False
        return mm >= current_month

    @staticmethod
    def name_valid(name: str) -> bool:
        v = re.sub(r"\s+", " ", (name or "").strip())
        parts = v.split(" ")
        if len(parts) < 2:
            return False
        return all(len(p) >= 2 for p in parts)

    @staticmethod
    def validate(name: str, number: str, expiry: str, cvv: str) -> list[str]:
        errors = []
        if not CardValidator.name_valid(name):
            errors.append("payment.invalidCardHolderName")
        digits = CardValidator._digits_only(number)
        if len(digits) < 15 or len(digits) > 19 or not CardValidator.luhn_check(digits):
            errors.append("payment.invalidCardNumber")
        if not CardValidator.expiry_valid(expiry):
            errors.append("payment.invalidExpiry")
        if not re.match(r"^\d{3,4}$", (cvv or "").strip()):
            errors.append("payment.invalidCvv")
        return errors

    @staticmethod
    def mask_or_format(number: str) -> str:
        # UI-friendly (comme Flutter spacing). Jamais retourner brut si tu ne veux pas.
        digits = CardValidator._digits_only(number)
        out = []
        for i, ch in enumerate(digits[:19]):
            if i and i % 4 == 0:
                out.append(" ")
            out.append(ch)
        return "".join(out)


# ---------------------------
# services/idempotency_service.py
# ---------------------------
# Simple mémoire (remplace par Redis/DB plus tard)
_idem_store: dict[str, dict] = {}

class IdempotencyService:
    @staticmethod
    def get_result(key: str) -> dict | None:
        return _idem_store.get(key)

    @staticmethod
    def store_result(key: str, payload: dict) -> None:
        _idem_store[key] = payload


# ---------------------------
# services/order_service.py
# ---------------------------
import uuid
from datetime import datetime

class OrderService:
    @staticmethod
    def build_success_payload(amount: str) -> dict:
        now = datetime.now()
        return {
            "amount": amount,
            "orderNumber": str(int(now.timestamp() * 1000)),
            "reference": str(uuid.uuid4()).replace("-", "")[:16].upper(),
            "date": now.strftime("%d/%m/%Y • %H:%M"),
        }

    @staticmethod
    def maybe_store_card_tokenized(save_card: bool, number: str, expiry: str) -> None:
        # IMPORTANT: ne jamais stocker number/cvv en clair.
        # Ici on ne stocke rien: brancher Stripe plus tard (tokenization).
        return
    
    # ---------------------------
# Feature: Get operators by country
# ---------------------------

def get_reloadly_operators_by_country(country_iso: str) -> list:

    token = os.environ.get("RELOADLY_ACCESS_TOKEN")

    if not token:
        return []

    url = f"https://topups.reloadly.com/operators/countries/{country_iso.upper()}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/com.reloadly.topups-v1+json"
    }

    try:

        res = requests.get(url, headers=headers, timeout=15)

        if res.status_code != 200:
            return []

        data = res.json()

    except Exception:
        return []

    operators = []

    for op in data:

        logos = op.get("logoUrls") or []

        logo_url = None
        if logos:
            if isinstance(logos[0], dict):
                logo_url = logos[0].get("url")
            else:
                logo_url = logos[0]

        operators.append({
            "id": op.get("operatorId"),
            "name": op.get("name"),
            "country": (op.get("country") or {}).get("name"),
            "country_iso": (op.get("country") or {}).get("isoName"),
            "logo_url": logo_url
        })

    return operators