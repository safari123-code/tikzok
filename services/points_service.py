# ---------------------------
# Points Service
# ---------------------------

class PointsService:
    """
    Gestion des points utilisateur.
    Version simple (mock).
    Prête à connecter à une base de données plus tard.
    """

    _mock_points = 0.0  # tu peux changer pour tester

    @staticmethod
    def get_points() -> float:
        """
        Retourne le nombre de points disponibles.
        """
        return float(PointsService._mock_points)

    @staticmethod
    def add_points(amount: float) -> None:
        """
        Ajoute des points (ex: 2.5% du montant).
        """
        PointsService._mock_points += float(amount)

    @staticmethod
    def use_points(amount: float) -> None:
        """
        Déduit des points utilisés.
        """
        PointsService._mock_points = max(
            0.0,
            PointsService._mock_points - float(amount)
        )

    @staticmethod
    def refresh() -> None:
        """
        Placeholder pour future synchronisation DB.
        """
        return