"""
Classe principale per il processamento dei dati FantaCalcio.
Wrapper per mantenere la compatibilità con il codice esistente.
"""
from src.data.calculator import StatsCalculator


class FantaCalcioDataProcessor:
    """Wrapper per StatsCalculator per compatibilità"""

    def __init__(self):
        self.calculator = StatsCalculator()

    def calculate_weighted_stats(self):
        """Calcola le statistiche ponderate"""
        return self.calculator.calculate_weighted_stats()

    def calculate_overall_scores(self, df):
        """Calcola gli Overall scores"""
        return self.calculator.calculate_overall_scores(df)
