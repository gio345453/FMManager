"""
Settings manager per configurazioni persistenti dell'applicazione
Include giornata corrente per fixture difficulty
"""
import json
from pathlib import Path
from typing import Optional


class SettingsManager:
    """Gestisce le impostazioni persistenti dell'applicazione"""

    def __init__(self):
        self.settings_file = Path('data/config/settings.json')
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        """Carica impostazioni da file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore caricamento settings: {e}")
                return self._default_settings()
        return self._default_settings()

    def _default_settings(self) -> dict:
        """Impostazioni di default"""
        return {
            'current_matchday': 1,  # Giornata corrente (1-38)
            'last_updated': None
        }

    def _save_settings(self):
        """Salva impostazioni su file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio settings: {e}")

    def get_current_matchday(self) -> int:
        """
        Ottiene la giornata corrente

        Returns:
            int: Giornata corrente (1-38)
        """
        return self.settings.get('current_matchday', 1)

    def set_current_matchday(self, matchday: int):
        """
        Imposta la giornata corrente

        Args:
            matchday: Numero giornata (1-38)
        """
        if 1 <= matchday <= 38:
            self.settings['current_matchday'] = matchday
            from datetime import datetime
            self.settings['last_updated'] = datetime.now().isoformat()
            self._save_settings()
        else:
            raise ValueError("Matchday deve essere tra 1 e 38")

    def get_all_settings(self) -> dict:
        """Ottiene tutte le impostazioni"""
        return self.settings.copy()


# Singleton globale
_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Ottiene istanza singleton del settings manager"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_current_matchday() -> int:
    """
    Helper function per ottenere la giornata corrente

    Returns:
        int: Giornata corrente (1-38)
    """
    return get_settings_manager().get_current_matchday()


def set_current_matchday(matchday: int):
    """
    Helper function per impostare la giornata corrente

    Args:
        matchday: Numero giornata (1-38)
    """
    get_settings_manager().set_current_matchday(matchday)
