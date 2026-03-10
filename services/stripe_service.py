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
    def create_payment_intent(amount: float, currency: str = "eur"):

        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            payment_method_types=["card"],
        )

        return intent

    # ---------------------------
    # Retrieve Payment
    # ---------------------------
    @staticmethod
    def retrieve_payment(payment_id: str):

        return stripe.PaymentIntent.retrieve(payment_id)