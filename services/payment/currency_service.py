# ---------------------------
# Currency Service (RELOADLY ONLY)
# ---------------------------

class CurrencyService:

    PREFIX_TO_CURRENCY = {
        "+33": "EUR",
        "+44": "GBP",
        "+1": "USD",
        "+93": "AFN",
        "+212": "MAD",
        "+225": "XOF",
        "+237": "XAF",
        "+234": "NGN",
        "+90": "TRY",
    }

    # ---------------------------
    # UI / STRIPE ONLY
    # ---------------------------
    @staticmethod
    def currency_from_phone(phone: str) -> str:
        if not phone:
            return "EUR"

        phone = phone.strip()

        # tri pour éviter collision (+1 vs +123)
        for prefix in sorted(CurrencyService.PREFIX_TO_CURRENCY.keys(), key=len, reverse=True):
            if phone.startswith(prefix):
                return CurrencyService.PREFIX_TO_CURRENCY[prefix]

        return "EUR"

    # ---------------------------
    # 🔥 SOURCE UNIQUE = RELOADLY
    # ---------------------------
    @staticmethod
    def received_display_value(phone, amount, selected_forfait, quote):

        # ---------------------------
        # PRIORITÉ forfait (UX)
        # ---------------------------
        if selected_forfait and selected_forfait.get("gb"):
            return f"{selected_forfait['gb']} GB"

        # ---------------------------
        # RELOADLY
        # ---------------------------
        if not quote:
            return "—"

        try:
            # destinationAmount = meilleur signal (final réel reçu)
            destination_amount = quote.get("destinationAmount")
            destination_currency = quote.get("destinationCurrencyCode")

            if destination_amount and destination_currency:
                return f"{CurrencyService._format_amount(destination_amount)} {destination_currency}"

            # fallback local
            local_amount = quote.get("localAmount")
            local_currency = quote.get("localCurrency")

            if local_amount and local_currency:
                return f"{CurrencyService._format_amount(local_amount)} {local_currency}"

        except Exception as e:
            print("❌ Currency parse error:", e)

        return "—"

    # ---------------------------
    # Internal helpers
    # ---------------------------
    @staticmethod
    def _format_amount(value):
        """
        Format propre:
        - évite 10.0
        - garde décimales utiles
        """
        try:
            value = float(value)
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip("0").rstrip(".")
        except:
            return "0"