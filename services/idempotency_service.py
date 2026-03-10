# ---------------------------
# Idempotency Service
# ---------------------------

class IdempotencyService:
    """
    Empêche le double paiement si l'utilisateur recharge
    la page ou clique plusieurs fois.
    Version mémoire (à remplacer par Redis/DB en prod).
    """

    _store = {}

    @staticmethod
    def get_result(key: str):
        """
        Retourne le résultat déjà enregistré pour cette clé.
        """
        return IdempotencyService._store.get(key)

    @staticmethod
    def store_result(key: str, payload: dict):
        """
        Stocke le résultat d'un paiement réussi.
        """
        if key:
            IdempotencyService._store[key] = payload