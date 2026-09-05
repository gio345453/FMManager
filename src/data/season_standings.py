"""Load standings from the versioned seasonal dataset with a legacy fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.data.team_strength_data import standings_from_mapping


STANDINGS_PATH = Path(__file__).parent.parent.parent / 'data' / 'Calendario' / 'season_standings.json'


def load_previous_season_standings(path: Path = STANDINGS_PATH) -> Dict[str, Dict[str, Any]]:
    if path.exists():
        with open(path, 'r', encoding='utf-8') as file:
            payload = json.load(file)
        teams = payload.get('teams', {}) if isinstance(payload, dict) else {}
        standings = standings_from_mapping(teams)
        if standings:
            return standings
    from src.data.team_stats import CLASSIFICA_REALE_CURRENT_SEASON

    return standings_from_mapping(CLASSIFICA_REALE_CURRENT_SEASON)
