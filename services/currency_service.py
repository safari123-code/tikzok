# ---------------------------
# Currency Service (Production Ready)
# ---------------------------

class CurrencyService:
    """
    Gère la devise + estimation fallback.
    Priorité:
    1. Forfait
    2. Reloadly quote
    3. Fallback interne sécurisé
    """

    # ---------------------------
    # Préfixe téléphone → devise
    # ---------------------------
    _country_currency_by_prefix = {
        "+33": "EUR",
        "+44": "GBP",
        "+1": "USD",
        "+93": "AFN",
        "+212": "MAD",
        "+225": "XOF",
        "+237": "XAF",
        "+234": "NGN",
    }

    # ---------------------------
    # Taux fallback (safe)
    # ---------------------------
    _fallback_rates = {
        "EUR": 1,
        "USD": 1,
        "GBP": 1,
        "AFN": 68.10,
        "MAD": 10,
        "XOF": 650,
        "XAF": 650,
        "NGN": 1400,
    }

    # ---------------------------
    # Devise depuis téléphone
    # ---------------------------
    @staticmethod
    def currency_from_phone(phone: str) -> str:

        if not phone:
            return "EUR"

        # 🔥 FIX: priorité aux préfixes longs
        for prefix in sorted(
            CurrencyService._country_currency_by_prefix.keys(),
            key=len,
            reverse=True
        ):
            if phone.startswith(prefix):
                return CurrencyService._country_currency_by_prefix[prefix]

        return "EUR"

    # ---------------------------
    # Taux fallback
    # ---------------------------
    @staticmethod
    def rate_from_currency(currency: str) -> float:

        return CurrencyService._fallback_rates.get(currency, 1)

    # ---------------------------
    # Estimation locale
    # ---------------------------
    @staticmethod
    def estimate_local_amount(phone: str, amount: float) -> tuple[float, str]:

        currency = CurrencyService.currency_from_phone(phone)
        rate = CurrencyService.rate_from_currency(currency)

        # 🔥 FIX: précision money
        local = round(amount * rate, 2)

        return local, currency

    # ---------------------------
    # Format affichage (UX pro)
    # ---------------------------
    @staticmethod
    def format_amount(value: float) -> str:
        return f"{value:,.2f}"

    # ---------------------------
    # Affichage "ils reçoivent"
    # ---------------------------
    @staticmethod
    def received_display_value(
        phone: str,
        amount: float,
        selected_forfait: dict | None,
        quote: dict | None,
    ) -> str:

        # ---------------------------
        # 1. Forfait (priorité)
        # ---------------------------
        if selected_forfait and selected_forfait.get("gb"):
            return str(selected_forfait["gb"])

        # ---------------------------
        # 2. Reloadly quote (source réelle)
        # ---------------------------
        if quote and quote.get("localAmount") and quote.get("localCurrency"):

            try:
                local_amount = float(quote["localAmount"])
            except Exception:
                local_amount = 0

            currency = quote["localCurrency"]

            return f"{CurrencyService.format_amount(local_amount)} {currency}"

        # ---------------------------
        # 3. Fallback estimation
        # ---------------------------
        local, currency = CurrencyService.estimate_local_amount(phone, amount)

        return f"{CurrencyService.format_amount(local)} {currency}"