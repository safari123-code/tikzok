# ---------------------------
# Credit Service
# ---------------------------

from services.user.user_service import UserService


class CreditService:

    BONUS_RATE = 0.025

    # ---------------------------
    # calculate bonus
    # ---------------------------
    @staticmethod
    def calculate_bonus(amount: float) -> float:

        try:
            amount = float(amount)
        except Exception:
            return 0.0

        if amount <= 0:
            return 0.0

        bonus = amount * CreditService.BONUS_RATE

        return round(bonus, 2)

    # ---------------------------
    # add credit
    # ---------------------------
    @staticmethod
    def add_credit(user_id: str, amount: float):

        if not user_id:
            return 0.0

        bonus = CreditService.calculate_bonus(amount)

        if bonus <= 0:
            return 0.0

        UserService.add_balance(
            user_id=user_id,
            amount=bonus
        )

        return bonus

    # ---------------------------
    # get balance
    # ---------------------------
    @staticmethod
    def get_balance(user_id: str):

        if not user_id:
            return 0.0

        return UserService.get_balance(user_id)