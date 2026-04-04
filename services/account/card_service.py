# ---------------------------
# Card Service (PRODUCTION)
# ---------------------------

class CardService:

    # ---------------------------
    # Save card
    # ---------------------------
    @staticmethod
    def save_card(user_id: str, payment_method):

        card = {
            "id": payment_method.id,
            "user_id": user_id,
            "brand": payment_method.card.brand,
            "last4": payment_method.card.last4,
            "expiry": f"{payment_method.card.exp_month}/{payment_method.card.exp_year}"
        }

        # ⚠️ À adapter à ta DB
        DB.insert("cards", card)

    # ---------------------------
    # Get user cards
    # ---------------------------
    @staticmethod
    def get_user_cards(user_id: str):

        return DB.find("cards", {"user_id": user_id})

    # ---------------------------
    # Delete card
    # ---------------------------
    @staticmethod
    def delete_card(card_id: str):

        DB.delete("cards", {"id": card_id})