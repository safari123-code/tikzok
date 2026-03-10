# ---------------------------
# Feature: Pricing Service
# ---------------------------

class PricingService:
    """
    Calcule les montants financiers de la recharge
    """

    @staticmethod
    def compute(amount: float, tax_rate: float, reloadly_cost: float | None = None):
        """
        amount = montant choisi par le client
        tax_rate = frais Tikzok
        reloadly_cost = coût réel Reloadly (si disponible)
        """

        tax = round(amount * tax_rate, 2)
        total = round(amount + tax, 2)

        profit = None

        if reloadly_cost is not None:
            profit = round(total - reloadly_cost, 2)

        return {
            "amount": amount,
            "tax": tax,
            "total": total,
            "reloadly_cost": reloadly_cost,
            "profit": profit
        }