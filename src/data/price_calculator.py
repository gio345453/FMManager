"""
Wrapper per compatibilità con il vecchio import
Import: from src.data.price_calculator import PriceCalculator
"""
from src.data.calculators.price_calculator import PriceCalculator

__all__ = ['PriceCalculator']
