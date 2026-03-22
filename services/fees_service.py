# ---------------------------
# Feature: Fees Service (Production Ready)
# ---------------------------

class FeesService:
    """
    Centralise le calcul des frais Tikzok.
    Compatible production (Stripe + Reloadly).
    """

    # ---------------------------
    # Default rate
    # ---------------------------
    DEFAULT_RATE = 0.20  # 20 %

    # ---------------------------
    # Rates par devise
    # ---------------------------
    CURRENCY_FEES = {
        "AFN": 0.01,
        "MAD": 0.22,
        "XOF": 0.20,
        "NGN": 0.23,
        "EUR": 0.18,
    }

    # ---------------------------
    # Get tax rate
    # ---------------------------
    @classmethod
    def get_tax_rate(cls, currency: str) -> float:

        if not currency:
            return cls.DEFAULT_RATE

        return cls.CURRENCY_FEES.get(currency.upper(), cls.DEFAULT_RATE)

    # ---------------------------
    # Compute tax (safe money)
    # ---------------------------
    @staticmethod
    def compute_tax(amount: float, rate: float) -> float:

        try:
            amount = float(amount)
        except Exception:
            return 0.0

        return round(amount * rate, 2)

    # ---------------------------
    # Compute total (safe)
    # ---------------------------
    @staticmethod
    def compute_total(amount: float, rate: float) -> float:

        try:
            amount = float(amount)
        except Exception:
            return 0.0

        total = amount + (amount * rate)

        return round(total, 2)

    # ---------------------------
    # Full breakdown (PRO)
    # ---------------------------
    @classmethod
    def breakdown(cls, amount: float, currency: str) -> dict:
        """
        Retourne un breakdown complet pour UI / API.
        """

        rate = cls.get_tax_rate(currency)

        tax = cls.compute_tax(amount, rate)
        total = cls.compute_total(amount, rate)

        return {
            "amount": round(amount, 2),
            "tax_rate": rate,
            "tax": tax,
            "total": total
        }