# ---------------------------
# Currency Service (FINAL PRO)
# ---------------------------

from services.fees_service import FeesService


class CurrencyService:
    """
    Gère la devise et l'estimation du montant reçu.
    Compatible business (fees + payout réel).
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
        "AFN": 80.33,
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

        for prefix, currency in CurrencyService._country_currency_by_prefix.items():
            if phone.startswith(prefix):
                return currency

        return "EUR"

    # ---------------------------
    # Taux fallback sécurisé
    # ---------------------------
    @staticmethod
    def rate_from_currency(currency: str) -> float:
        return CurrencyService._fallback_rates.get(currency, 1)

    # ---------------------------
    # Calcul estimation locale (NET)
    # ---------------------------
    @staticmethod
    def estimate_local_amount(phone: str, amount: float) -> tuple[int, str]:

        currency = CurrencyService.currency_from_phone(phone)
        rate = CurrencyService.rate_from_currency(currency)

        # 🔥 appliquer payout réel (après frais)
        payout_data = FeesService.compute_payout(amount, currency)
        payout = payout_data["payout"]

        local = round(payout * rate)

        return local, currency

    # ---------------------------
    # Affichage "Ils reçoivent"
    # ---------------------------
    @staticmethod
    def received_display_value(
        phone: str,
        amount: float,
        selected_forfait: dict | None,
        quote: dict | None,
    ) -> str:

        # ---------------------------
        # DATA forfait prioritaire
        # ---------------------------
        if selected_forfait and selected_forfait.get("gb"):
            return str(selected_forfait["gb"])

        currency = CurrencyService.currency_from_phone(phone)

        # ---------------------------
        # Reloadly quote (corrigé fees)
        # ---------------------------
        if quote and quote.get("localAmount") and quote.get("localCurrency"):

            payout_data = FeesService.compute_payout(amount, currency)

            ratio = payout_data["payout"] / amount if amount else 1

            local_amount = int(float(quote["localAmount"]) * ratio)

            return f"{local_amount} {quote['localCurrency']}"

        # ---------------------------
        # Fallback estimation
        # ---------------------------
        local, currency = CurrencyService.estimate_local_amount(phone, amount)

        return f"{local} {currency}"