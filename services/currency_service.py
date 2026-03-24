# ---------------------------
# Currency Service (FINAL PRO - RELOADLY READY)
# ---------------------------

class CurrencyService:

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
    # Taux manuel (fallback)
    # ---------------------------
    _manual_rates = {
        "EUR": 1,
        "USD": 1.1,
        "GBP": 0.85,
        "AFN": 65.10,
        "MAD": 10.4,
        "XOF": 655,
        "XAF": 655,
        "NGN": 1500,
    }

    # ---------------------------
    # Devise depuis téléphone
    # ---------------------------
    @staticmethod
    def currency_from_phone(phone: str) -> str:

        if not phone:
            return "EUR"

        for prefix, currency in CurrencyService._country_currency_by_prefix.items():
            if phone.startswith(prefix):
                return currency

        return "EUR"

    # ---------------------------
    # Taux (fallback uniquement)
    # ---------------------------
    @staticmethod
    def rate_from_currency(currency: str) -> float:
        return CurrencyService._manual_rates.get(currency, 1)

    # ---------------------------
    # ESTIMATION (fallback only)
    # ---------------------------
    @staticmethod
    def estimate_local_amount(phone: str, amount: float):

        currency = CurrencyService.currency_from_phone(phone)
        rate = CurrencyService.rate_from_currency(currency)

        local = amount * rate

        return int(round(local)), currency

    # ---------------------------
    # Affichage final (SOURCE OF TRUTH = RELOADLY)
    # ---------------------------
    @staticmethod
    def received_display_value(phone, amount, selected_forfait, quote):

        # ---------------------------
        # PRIORITÉ UX : forfait data
        # ---------------------------
        if selected_forfait and selected_forfait.get("gb"):
            return str(selected_forfait["gb"])

        # ---------------------------
        # ✅ PRIORITÉ ABSOLUE : Reloadly
        # ---------------------------
        if quote:

            try:
                # 🔥 vrai montant reçu utilisateur
                if quote.get("destinationAmount") and quote.get("destinationCurrencyCode"):
                    return f"{int(float(quote['destinationAmount']))} {quote['destinationCurrencyCode']}"

                # 🔥 fallback Reloadly
                if quote.get("localAmount") and quote.get("localCurrency"):
                    return f"{int(float(quote['localAmount']))} {quote['localCurrency']}"

            except Exception as e:
                print("❌ CurrencyService parse error:", e)

        # ---------------------------
        # Fallback interne (sécurité)
        # ---------------------------
        local, currency = CurrencyService.estimate_local_amount(phone, amount)

        return f"{local} {currency}"