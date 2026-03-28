# ---------------------------
# Card Validator Service (TEST MODE)
# ---------------------------

import re


class CardValidator:
    """
    Mode TEST
    Toutes les cartes sont acceptées pour tester le flow paiement.
    ⚠️ À réactiver avant production.
    """

    # ---------------------------
    # Validation (disabled for testing)
    # ---------------------------
    @staticmethod
    def validate(name: str, number: str, expiry: str, cvv: str):
        # Toujours accepter
        return []

    # ---------------------------
    # Mask card for display
    # ---------------------------
    @staticmethod
    def mask_or_format(number: str):

        digits = re.sub(r"\D", "", number or "")

        if len(digits) >= 4:
            return "**** **** **** " + digits[-4:]

        return ""