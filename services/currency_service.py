# ---------------------------
# Currency Service
# ---------------------------

class CurrencyService:
    """
    Gère la devise et l'estimation du montant reçu.
    Utilisé si Reloadly quote n'est pas disponible.
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
    # Taux fallback approximatifs
    # ---------------------------
    _fallback_rates = {
        "EUR": 1,
        "USD": 1,
        "GBP": 1,
        "AFN": 70.33,
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
        """
        Déduit la devise à partir du préfixe du numéro.
        """

        if not phone:
            return "EUR"

        for prefix, currency in CurrencyService._country_currency_by_prefix.items():
            if phone.startswith(prefix):
                return currency

        return "EUR"

    # ---------------------------
    # Taux fallback sécurisé
    # ---------------------------
    @staticmethod
    def rate_from_currency(currency: str) -> float:
        """
        Retourne le taux fallback sécurisé.
        """

        return CurrencyService._fallback_rates.get(currency, 1)

    # ---------------------------
    # Calcul estimation locale
    # ---------------------------
    @staticmethod
    def estimate_local_amount(phone: str, amount: float) -> tuple[int, str]:

        currency = CurrencyService.currency_from_phone(phone)
        rate = CurrencyService.rate_from_currency(currency)

        local = round(amount * rate)

        return local, currency

    # ---------------------------
    # Affichage "Ils/Elles reçoivent"
    # ---------------------------
    @staticmethod
    def received_display_value(
        phone: str,
        amount: float,
        selected_forfait: dict | None,
        quote: dict | None,
    ) -> str:

        # ---------------------------
        # Forfait prioritaire
        # ---------------------------
        if selected_forfait and selected_forfait.get("gb"):
            return str(selected_forfait["gb"])

        # ---------------------------
        # Reloadly quote
        # ---------------------------
        if quote and quote.get("localAmount") and quote.get("localCurrency"):

            local_amount = int(float(quote["localAmount"]))
            currency = quote["localCurrency"]

            return f"{local_amount} {currency}"

        # ---------------------------
        # Fallback estimation
        # ---------------------------
        local, currency = CurrencyService.estimate_local_amount(phone, amount)

        return f"{local} {currency}"