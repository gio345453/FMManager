"""Contratto unico per le configurazioni che influenzano i motori di gioco.

Questo modulo è intenzionalmente privo di dipendenze web: sia il LineupService
sia la simulazione stagionale ricevono qui gli stessi valori normalizzati.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping


DEFAULT_FORMATIONS: Dict[str, Dict[str, int]] = {
    "3-4-3": {"P": 1, "D": 3, "C": 4, "A": 3},
    "3-5-2": {"P": 1, "D": 3, "C": 5, "A": 2},
    "4-3-3": {"P": 1, "D": 4, "C": 3, "A": 3},
    "4-4-2": {"P": 1, "D": 4, "C": 4, "A": 2},
    "4-5-1": {"P": 1, "D": 4, "C": 5, "A": 1},
    "5-3-2": {"P": 1, "D": 5, "C": 3, "A": 2},
    "5-4-1": {"P": 1, "D": 5, "C": 4, "A": 1},
}

DEFAULT_ROSTER_COMPOSITION = {"P": 3, "D": 8, "C": 8, "A": 6}


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class LeagueConfig:
    """Impostazioni canonicali della lega e relative viste per i servizi."""

    starting_budget: float = 500.0
    participants: int = 10
    min_price: float = 1.0
    bid_increment: float = 1.0
    reserve: float = 0.0
    scoring: Dict[str, float] = field(default_factory=lambda: {
        "goal_bonus": 3.0,
        "assist_bonus": 1.0,
        "yellow_card_malus": 0.5,
        "red_card_malus": 1.0,
        "own_goal_malus": 2.0,
        "clean_sheet_bonus": 1.0,
        "goal_threshold": 66.0,
        "points_per_goal": 4.0,
    })
    formations: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: {name: dict(roles) for name, roles in DEFAULT_FORMATIONS.items()}
    )
    roster_composition: Dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_ROSTER_COMPOSITION)
    )

    @classmethod
    def from_settings(cls, settings: Mapping[str, Any] | None = None) -> "LeagueConfig":
        """Converte il formato persistito dell'app nel contratto dei motori."""
        settings = settings or {}
        bonus = settings.get("bonus", {}) if isinstance(settings.get("bonus", {}), Mapping) else {}
        scoring_config = settings.get("scoring", {}) if isinstance(settings.get("scoring", {}), Mapping) else {}

        scoring = {
            "goal_bonus": _number(bonus.get("gol"), 3.0),
            "assist_bonus": _number(bonus.get("assist"), 1.0),
            "yellow_card_malus": abs(_number(bonus.get("ammonizione"), -0.5)),
            "red_card_malus": abs(_number(bonus.get("espulsione"), -1.0)),
            "own_goal_malus": abs(_number(bonus.get("autogol"), -2.0)),
            "clean_sheet_bonus": _number(bonus.get("clean_sheet_portiere"), 1.0),
            "goal_threshold": _number(scoring_config.get("goal_threshold"), 66.0),
            "points_per_goal": _number(scoring_config.get("points_per_goal"), 4.0),
        }
        formations = settings.get("formations")
        if not isinstance(formations, Mapping) or not formations:
            formations = DEFAULT_FORMATIONS
        composition = settings.get("roster_composition")
        if not isinstance(composition, Mapping) or not composition:
            composition = DEFAULT_ROSTER_COMPOSITION
        return cls(
            starting_budget=_number(settings.get("budget"), 500.0),
            participants=max(2, int(_number(settings.get("participants"), 10))),
            min_price=max(0.0, _number(settings.get("min_price"), 1.0)),
            bid_increment=max(0.01, _number(settings.get("bid_increment"), 1.0)),
            reserve=max(0.0, _number(settings.get("reserve"), 0.0)),
            scoring=scoring,
            formations={str(name): {str(role): int(count) for role, count in roles.items()} for name, roles in formations.items()},
            roster_composition={str(role): int(count) for role, count in composition.items()},
        )

    def lineup_options(self, overrides: Mapping[str, Any] | None = None) -> Dict[str, float]:
        """Restituisce l'unica vista punteggi usata dal LineupService."""
        options = dict(self.scoring)
        for key, value in (overrides or {}).items():
            if key in options:
                options[key] = _number(value, options[key])
        return options
