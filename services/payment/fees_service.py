# ---------------------------
# Feature: Fees Service (FINAL FIXED - MARKUP MODEL)
# ---------------------------

class FeesService:
    """
    Centralise le calcul des frais Tikzok.
    Modèle: MARKUP (client paie plus, payout intact).
    """

    # ---------------------------
    # Default rate
    # ---------------------------
    DEFAULT_RATE = 0.20  # 20 %

    # ---------------------------
    # Rates par devise
    # ---------------------------
    CURRENCY_FEES = {
        "AFN": 0.20,
        "MAD": 0.22,
        "XOF": 0.20,
        "NGN": 0.23,
        "EUR": 0.18,
    }

    # ---------------------------
    # Minimum fee
    # ---------------------------
    MIN_FEE = 0.20

    # ---------------------------
    # Get tax rate
    # ---------------------------
    @classmethod
    def get_tax_rate(cls, currency: str) -> float:

        if not currency:
            return cls.DEFAULT_RATE

        return cls.CURRENCY_FEES.get(currency.upper(), cls.DEFAULT_RATE)

    # ---------------------------
    # Compute fee (NEW SAFE CORE)
    # ---------------------------
    @classmethod
    def compute_fee(cls, amount: float, rate: float) -> float:

        try:
            amount = float(amount)
        except Exception:
            return 0.0

        fee = round(amount * rate, 2)

        # minimum garanti
        return max(fee, cls.MIN_FEE)

    # ---------------------------
    # Compute tax (compat)
    # ---------------------------
    @staticmethod
    def compute_tax(amount: float, rate: float) -> float:
        try:
            amount = float(amount)
        except Exception:
            return 0.0

        return round(amount * rate, 2)

    # ---------------------------
    # Compute total (client paie)
    # ---------------------------
    @classmethod
    def compute_total(cls, amount: float, rate: float) -> float:

        try:
            amount = float(amount)
        except Exception:
            return 0.0

        fee = cls.compute_fee(amount, rate)

        return round(amount + fee, 2)

    # ---------------------------
    # Full breakdown (UI SAFE)
    # ---------------------------
    @classmethod
    def breakdown(cls, amount: float, currency: str) -> dict:

        try:
            amount = float(amount)
        except Exception:
            amount = 0.0

        rate = cls.get_tax_rate(currency)

        fee = cls.compute_fee(amount, rate)
        total = round(amount + fee, 2)

        return {
            "amount": round(amount, 2),
            "tax_rate": rate,
            "tax": fee,  # garde compat naming
            "total": total
        }

    # ---------------------------
    # Compute payout (FIX CRITIQUE)
    # ---------------------------
    @classmethod
    def compute_payout(cls, amount: float, currency: str) -> dict:
        """
        Modèle MARKUP:
        - client paie plus
        - payout = amount (intouché)
        """

        try:
            amount = float(amount)
        except Exception:
            return {
                "paid": 0.0,
                "fee": 0.0,
                "payout": 0.0,
                "rate": 0.0
            }

        rate = cls.get_tax_rate(currency)

        fee = cls.compute_fee(amount, rate)

        total = round(amount + fee, 2)

        return {
            "paid": total,     # 🔥 client paie total
            "fee": fee,        # 🔥 ta marge
            "payout": round(amount, 2),  # 🔥 ENVOYÉ À RELOADLY
            "rate": rate
        }