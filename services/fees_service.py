# ---------------------------
# Feature: Fees Service
# ---------------------------

class FeesService:
    """
    Centralise le calcul des frais Tikzok.
    """

    # taux par défaut (modifiable facilement)
    DEFAULT_RATE = 0.20  # 20 %

    # surcharge possible par devise
    CURRENCY_FEES = {
        "AFN": 0.10,
        "MAD": 0.22,
        "XOF": 0.20,
        "NGN": 0.23,
        "EUR": 0.18,
    }

    @classmethod
    def get_tax_rate(cls, currency: str) -> float:
        """
        Retourne le taux de frais selon la devise.
        """
        if not currency:
            return cls.DEFAULT_RATE

        return cls.CURRENCY_FEES.get(currency, cls.DEFAULT_RATE)

    @staticmethod
    def compute_tax(amount: float, rate: float) -> float:
        """
        Calcule le montant des frais.
        """
        return round(amount * rate, 2)

    @staticmethod
    def compute_total(amount: float, rate: float) -> float:
        """
        Montant total payé par le client.
        """
        return round(amount + (amount * rate), 2)