# ---------------------------
# Stripe Service
# ---------------------------

import stripe
import config


stripe.api_key = config.STRIPE_SECRET_KEY


class StripeService:

    # ---------------------------
    # Create Payment Intent
    # ---------------------------
    @staticmethod
    def create_payment_intent(
        amount: float,
        currency: str = "eur",
        metadata: dict | None = None,
    ):

        safe_amount = max(float(amount), 0.50)
        unit_amount = int(round(safe_amount * 100))

        intent = stripe.PaymentIntent.create(
            amount=unit_amount,
            currency=currency,
            metadata=metadata or {},
            automatic_payment_methods={"enabled": True},
            idempotency_key=(metadata or {}).get("payment_idempotency_key")
        )

        return intent

    # ---------------------------
    # Retrieve Payment Intent
    # ---------------------------
    @staticmethod
    def retrieve_payment(payment_id: str):
        return stripe.PaymentIntent.retrieve(payment_id)

    # ---------------------------
    # Construct Webhook Event
    # ---------------------------
    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str):

        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=config.STRIPE_WEBHOOK_SECRET,
        )