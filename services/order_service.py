# ---------------------------
# Order Service
# ---------------------------

import uuid
import json
import os
import re
from datetime import datetime


CARDS_FILE = "data/saved_cards.json"


class OrderService:
    """
    Construit la réponse succès paiement
    et gère les cartes enregistrées.
    """

    # ---------------------------
    # Success payload
    # ---------------------------
    @staticmethod
    def build_success_payload(amount: str) -> dict:

        now = datetime.now()

        return {
            "amount": amount,
            "orderNumber": str(int(now.timestamp() * 1000)),
            "reference": uuid.uuid4().hex[:12].upper(),
            "date": now.strftime("%d/%m/%Y • %H:%M"),
        }

    # ---------------------------
    # Save card (tokenized)
    # ---------------------------
    @staticmethod
    def maybe_store_card_tokenized(save_card: bool, number: str, expiry: str):

        if not save_card:
            return

        digits = "".join(c for c in (number or "") if c.isdigit())

        if len(digits) < 4:
            return

        token = "tok_" + uuid.uuid4().hex[:16]
        last4 = digits[-4:]

        card = {
            "id": uuid.uuid4().hex,
            "token": token,
            "last4": last4,
            "expiry": expiry,
            "brand": "card",
            "created_at": datetime.utcnow().isoformat(),
        }

        OrderService._store_card(card)

    # ---------------------------
    # Internal storage
    # ---------------------------
    @staticmethod
    def _store_card(card):

        os.makedirs("data", exist_ok=True)

        cards = []

        if os.path.exists(CARDS_FILE):
            with open(CARDS_FILE, "r") as f:
                try:
                    cards = json.load(f)
                except Exception:
                    cards = []

        cards.append(card)

        with open(CARDS_FILE, "w") as f:
            json.dump(cards, f, indent=2)

    # ---------------------------
    # Get saved cards
    # ---------------------------
    @staticmethod
    def get_saved_cards():

        if not os.path.exists(CARDS_FILE):
            return []

        with open(CARDS_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return []

    # ---------------------------
    # Delete saved card
    # ---------------------------
    @staticmethod
    def delete_saved_card(user_id, card_id):

        cards = OrderService.get_saved_cards()

        cards = [c for c in cards if c["id"] != card_id]

        with open(CARDS_FILE, "w") as f:
            json.dump(cards, f, indent=2)

    # ---------------------------
    # Get card
    # ---------------------------
    @staticmethod
    def get_saved_card(user_id, card_id):

        cards = OrderService.get_saved_cards()

        for c in cards:
            if c["id"] == card_id:
                return c

        return None

    # ---------------------------
    # Set default card
    # ---------------------------
    @staticmethod
    def set_default_card(user_id, card_id):

        cards = OrderService.get_saved_cards()

        for c in cards:
            c["is_default"] = c["id"] == card_id

        with open(CARDS_FILE, "w") as f:
            json.dump(cards, f, indent=2)

    # ---------------------------
    # Update saved card
    # ---------------------------
    @staticmethod
    def update_saved_card(card_id: str, name: str, number: str, expiry: str):

        if not os.path.exists(CARDS_FILE):
            return

        with open(CARDS_FILE, "r") as f:
            try:
                cards = json.load(f)
            except Exception:
                cards = []

        digits = re.sub(r"\D", "", number or "")
        last4 = digits[-4:] if len(digits) >= 4 else None

        for c in cards:
            if c["id"] == card_id:

                if name:
                    c["name"] = name

                if last4:
                    c["last4"] = last4

                if expiry:
                    c["expiry"] = expiry

        with open(CARDS_FILE, "w") as f:
            json.dump(cards, f, indent=2)