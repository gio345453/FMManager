"""
Settings service - gestisce le impostazioni dell'applicazione
"""
import json
import os
from typing import Dict, Any
from pathlib import Path


class SettingsService:
    """Service per gestire le impostazioni dell'applicazione"""

    def __init__(self):
        # Usa path assoluto rispetto alla root del progetto
        # startup.py aggiunge root al sys.path, quindi "data/config" è relativo alla root
        base_path = Path(__file__).parent.parent.parent.parent  # Da services -> backend -> web -> root
        self.settings_file = base_path / "data" / "config" / "app_settings.json"
        print(f"DEBUG SettingsService: usando file {self.settings_file}")
        self.default_settings = {
            "budget": 500,
            "participants": 10,
            "roster_composition": {
                "P": 3,
                "D": 8,
                "C": 8,
                "A": 6
            },
            "formations": {
                "3-4-3": {"P": 1, "D": 3, "C": 4, "A": 3},
                "3-5-2": {"P": 1, "D": 3, "C": 5, "A": 2},
                "4-3-3": {"P": 1, "D": 4, "C": 3, "A": 3},
                "4-4-2": {"P": 1, "D": 4, "C": 4, "A": 2},
                "4-5-1": {"P": 1, "D": 4, "C": 5, "A": 1},
                "5-3-2": {"P": 1, "D": 5, "C": 3, "A": 2},
                "5-4-1": {"P": 1, "D": 5, "C": 4, "A": 1}
            },
            "bonus": {
                "gol": 3,
                "assist": 1,
                "rigore_parato": 3,
                "rigore_segnato": 3,
                "rigore_sbagliato": -3,
                "autogol": -2,
                "ammonizione": -0.5,
                "espulsione": -1,
                "clean_sheet_portiere_enabled": True,
                "clean_sheet_portiere": 1,
                "clean_sheet_difensore_enabled": False,
                "clean_sheet_difensore": 1
            },
            "coefficienti_gol": {
                "portiere": 1,
                "difensore": 2,
                "centrocampista": 2,
                "attaccante": 1
            },
            "scoring": {
                "goal_threshold": 66.0,
                "points_per_goal": 4.0
            }
        }

    def get_settings(self) -> Dict[str, Any]:
        """
        Ottiene le impostazioni correnti

        Returns:
            Dict con le impostazioni
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    print(f"DEBUG get_settings: Letto dal file, chiavi: {list(settings.keys())}")
                    # Merge con default per eventuali nuove chiavi
                    merged = self._merge_with_defaults(settings)
                    print(f"DEBUG get_settings: Dopo merge, chiavi: {list(merged.keys())}")
                    return merged
            else:
                # Crea file con impostazioni default
                self.save_settings(self.default_settings)
                return self.default_settings
        except Exception as e:
            print(f"Errore lettura impostazioni: {e}")
            return self.default_settings

    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Salva le impostazioni

        Args:
            settings: Dict con le impostazioni da salvare

        Returns:
            Dict con le impostazioni salvate
        """
        try:
            # Assicurati che la directory esista
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Valida e normalizza le impostazioni
            validated_settings = self._validate_settings(settings)

            print(f"DEBUG: Validating settings...")
            print(f"  roster_composition in validated: {'roster_composition' in validated_settings}")
            print(f"  scoring in validated: {'scoring' in validated_settings}")
            if 'roster_composition' in validated_settings:
                print(f"  roster_composition value: {validated_settings['roster_composition']}")
            if 'scoring' in validated_settings:
                print(f"  scoring value: {validated_settings['scoring']}")

            # Salva su file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(validated_settings, f, indent=2, ensure_ascii=False)

            print(f"OK Settings salvati su {self.settings_file}")
            return validated_settings
        except Exception as e:
            print(f"ERRORE salvataggio: {e}")
            raise ValueError(f"Errore salvataggio impostazioni: {e}")

    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida le impostazioni

        Args:
            settings: Dict da validare

        Returns:
            Dict validato
        """
        validated = {}

        # Budget
        validated['budget'] = max(100, min(5000, int(settings.get('budget', 500))))

        # Partecipanti
        validated['participants'] = max(2, min(20, int(settings.get('participants', 10))))

        # Composizione rosa
        roster = settings.get('roster_composition', {})
        validated['roster_composition'] = {
            'P': max(1, min(5, int(roster.get('P', 3)))),
            'D': max(4, min(12, int(roster.get('D', 8)))),
            'C': max(4, min(12, int(roster.get('C', 8)))),
            'A': max(3, min(10, int(roster.get('A', 6))))
        }

        # Formazioni
        formations = settings.get('formations', {})
        if isinstance(formations, dict) and formations:
            validated['formations'] = formations
        else:
            validated['formations'] = self.default_settings['formations']

        # Bonus
        bonus = settings.get('bonus', {})
        validated['bonus'] = {
            'gol': self._validate_number(bonus.get('gol', 3), -10, 10),
            'assist': self._validate_number(bonus.get('assist', 1), -10, 10),
            'rigore_parato': self._validate_number(bonus.get('rigore_parato', 3), -10, 10),
            'rigore_segnato': self._validate_number(bonus.get('rigore_segnato', 3), -10, 10),
            'rigore_sbagliato': self._validate_number(bonus.get('rigore_sbagliato', -3), -10, 10),
            'autogol': self._validate_number(bonus.get('autogol', -2), -10, 10),
            'ammonizione': self._validate_number(bonus.get('ammonizione', -0.5), -10, 10),
            'espulsione': self._validate_number(bonus.get('espulsione', -1), -10, 10),
            'clean_sheet_portiere_enabled': bool(bonus.get('clean_sheet_portiere_enabled', True)),
            'clean_sheet_portiere': self._validate_number(bonus.get('clean_sheet_portiere', 1), -10, 10),
            'clean_sheet_difensore_enabled': bool(bonus.get('clean_sheet_difensore_enabled', False)),
            'clean_sheet_difensore': self._validate_number(bonus.get('clean_sheet_difensore', 1), -10, 10),
        }

        # Coefficienti gol per ruolo
        coefficienti = settings.get('coefficienti_gol', {})
        validated['coefficienti_gol'] = {
            'portiere': self._validate_number(coefficienti.get('portiere', 1), 0.1, 10),
            'difensore': self._validate_number(coefficienti.get('difensore', 2), 0.1, 10),
            'centrocampista': self._validate_number(coefficienti.get('centrocampista', 2), 0.1, 10),
            'attaccante': self._validate_number(coefficienti.get('attaccante', 1), 0.1, 10),
        }

        # Scoring system
        scoring = settings.get('scoring', {})
        validated['scoring'] = {
            'goal_threshold': self._validate_number(scoring.get('goal_threshold', 66.0), 50.0, 100.0),
            'points_per_goal': self._validate_number(scoring.get('points_per_goal', 4.0), 1.0, 10.0)
        }

        return validated

    def _validate_number(self, value, min_val, max_val):
        """Valida un numero entro un range"""
        try:
            num = float(value)
            return max(min_val, min(max_val, num))
        except:
            return 0

    def _merge_with_defaults(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge impostazioni con default per nuove chiavi"""
        merged = {
            'budget': settings.get('budget', self.default_settings['budget']),
            'participants': settings.get('participants', self.default_settings['participants']),
            'roster_composition': {**self.default_settings['roster_composition'], **settings.get('roster_composition', {})},
            'formations': settings.get('formations', self.default_settings['formations']),
            'bonus': {**self.default_settings['bonus'], **settings.get('bonus', {})},
            'coefficienti_gol': {**self.default_settings['coefficienti_gol'], **settings.get('coefficienti_gol', {})},
            'scoring': {**self.default_settings['scoring'], **settings.get('scoring', {})}
        }
        return merged

    def get_budget(self) -> int:
        """Ottiene il budget configurato"""
        settings = self.get_settings()
        return settings.get('budget', 500)

    def get_participants(self) -> int:
        """Ottiene il numero di partecipanti configurato"""
        settings = self.get_settings()
        return settings.get('participants', 10)

    def get_bonus(self) -> Dict[str, Any]:
        """Ottiene i bonus/malus configurati"""
        settings = self.get_settings()
        return settings.get('bonus', self.default_settings['bonus'])

    def get_roster_composition(self) -> Dict[str, int]:
        """Ottiene la composizione rosa configurata"""
        settings = self.get_settings()
        return settings.get('roster_composition', self.default_settings['roster_composition'])

    def get_formations(self) -> Dict[str, Dict[str, int]]:
        """Ottiene le formazioni configurate"""
        settings = self.get_settings()
        return settings.get('formations', self.default_settings['formations'])

    def get_scoring(self) -> Dict[str, float]:
        """Ottiene le impostazioni di scoring"""
        settings = self.get_settings()
        return settings.get('scoring', self.default_settings['scoring'])
