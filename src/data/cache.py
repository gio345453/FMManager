"""
Cache per i dati CSV per evitare ricaricamenti multipli
"""
from functools import lru_cache
from src.data.csv_loader import load_csv_base


class DataCache:
    """Cache singleton per i file CSV"""

    _instance = None
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataCache, cls).__new__(cls)
        return cls._instance

    def get(self, filename):
        """
        Recupera un DataFrame dalla cache o lo carica se non presente

        Args:
            filename: Nome del file CSV

        Returns:
            DataFrame o None
        """
        if filename not in self._cache:
            self._cache[filename] = load_csv_base(filename)
        return self._cache[filename]

    def clear(self):
        """Svuota la cache"""
        self._cache.clear()
