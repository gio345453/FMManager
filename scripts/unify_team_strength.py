"""Unifica produzione recente, storico lungo, reparti e classifica."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.season_standings import load_previous_season_standings
from src.data.team_strength_data import clamp_strength, rank_strength, unwrap_teams


RECENT_WEIGHT = 0.40
DEPARTMENT_WEIGHT = 0.30
RANK_WEIGHT = 0.20
HISTORY_WEIGHT = 0.10


class UnifiedTeamStrengthCalculator:
    """Produce il dataset runtime mantenendo campi compatibili con i consumer."""

    def __init__(
        self,
        historical_file: str = "data/Calendario/team_historical_strength.json",
        department_strength_file: str = "data/Calendario/team_department_strength.json",
        output_file: str = "data/Calendario/team_strength.json",
        standings: Mapping[str, Mapping[str, Any]] | None = None,
    ):
        self.historical_file = Path(historical_file)
        self.department_strength_file = Path(department_strength_file)
        self.output_file = Path(output_file)
        self.standings = dict(standings) if standings is not None else load_previous_season_standings()

    @staticmethod
    def load_json(filepath: Path) -> dict[str, Any]:
        if not filepath.exists():
            print(f"Dataset non trovato: {filepath}")
            return {}
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _valid_strength(value: Any) -> float | None:
        try:
            return clamp_strength(float(value))
        except (TypeError, ValueError):
            return None

    def _rank_component(self, team: str) -> tuple[float | None, dict[str, Any]]:
        standing = self.standings.get(team)
        if standing:
            value = rank_strength(standing.get("position"), standing.get("participants"))
            if value is not None:
                return value, {
                    "previous_rank": int(standing["position"]),
                    "rank_participants": int(standing["participants"]),
                    "rank_strength": round(value, 3),
                    "strength_source": "previous_serie_a",
                    "is_promoted": False,
                }
        return None, {
            "previous_rank": None,
            "rank_participants": None,
            "rank_strength": None,
            "strength_source": "missing_previous_serie_a",
            "is_promoted": True,
        }

    @staticmethod
    def _blend(components: Mapping[str, tuple[float | None, float]]) -> tuple[float, dict[str, float], list[str]]:
        usable = {
            name: (value, weight)
            for name, (value, weight) in components.items()
            if value is not None
        }
        if not usable:
            return 5.0, {}, list(components)
        denominator = sum(weight for _, weight in usable.values())
        effective_weights = {
            name: round(weight / denominator, 4)
            for name, (_, weight) in usable.items()
        }
        score = sum(value * effective_weights[name] for name, (value, _) in usable.items())
        return clamp_strength(score), effective_weights, [name for name in components if name not in usable]

    @staticmethod
    def _historical_component(team: Mapping[str, Any], metric: str) -> float | None:
        return UnifiedTeamStrengthCalculator._valid_strength(
            team.get(metric, team.get(metric.replace("historical_", "")))
        )

    def merge_strengths(self, historical_data: Mapping[str, Any], department_data: Mapping[str, Any]) -> dict[str, Any]:
        historical = unwrap_teams(historical_data)
        departments = unwrap_teams(department_data)
        all_teams = sorted(set(historical) | set(departments) | set(self.standings))
        result: dict[str, Any] = {}

        for team_name in all_teams:
            historical_team = historical.get(team_name, {})
            department_team = departments.get(team_name, {})
            rank_value, metadata = self._rank_component(team_name)
            recent_attack = self._valid_strength(historical_team.get("recent_attack"))
            recent_defense = self._valid_strength(historical_team.get("recent_defense"))
            historical_attack = self._historical_component(historical_team, "historical_attack")
            historical_defense = self._historical_component(historical_team, "historical_defense")
            department_attack = self._valid_strength(department_team.get("attack"))
            department_defense = self._valid_strength(department_team.get("defense"))
            midfield = self._valid_strength(department_team.get("midfield"))

            attack, attack_weights, attack_missing = self._blend({
                "recent_production": (recent_attack, RECENT_WEIGHT),
                "department": (department_attack, DEPARTMENT_WEIGHT),
                "previous_rank": (rank_value, RANK_WEIGHT),
                "long_history": (historical_attack, HISTORY_WEIGHT),
            })
            defense, defense_weights, defense_missing = self._blend({
                "recent_production": (recent_defense, RECENT_WEIGHT),
                "department": (department_defense, DEPARTMENT_WEIGHT),
                "previous_rank": (rank_value, RANK_WEIGHT),
                "long_history": (historical_defense, HISTORY_WEIGHT),
            })
            if not attack_weights and not defense_weights:
                metadata["strength_source"] = "no_strength_sources"

            result[team_name] = {
                "attack": round(attack, 1),
                "defense": round(defense, 1),
                "midfield": round(midfield if midfield is not None else 5.0, 1),
                "overall": round(clamp_strength((attack + defense) / 2), 1),
                "components": {
                    "recent_attack": recent_attack,
                    "recent_defense": recent_defense,
                    "historical_attack": historical_attack,
                    "historical_defense": historical_defense,
                    "department_attack": department_attack,
                    "department_defense": department_defense,
                    "rank": round(rank_value, 3) if rank_value is not None else None,
                    "recent_season": historical_team.get("recent_season"),
                    "recent_source_quality": historical_team.get("recent_source_quality"),
                    "historical_attack_weights": historical_team.get("historical_attack_weights", []),
                    "historical_defense_weights": historical_team.get("historical_defense_weights", []),
                },
                "effective_weights": {
                    "attack": attack_weights,
                    "defense": defense_weights,
                },
                "missing_components": {
                    "attack": attack_missing,
                    "defense": defense_missing,
                },
                **metadata,
            }
        return result

    def save_to_json(self, data: Mapping[str, Any]) -> None:
        teams = dict(sorted(data.items(), key=lambda item: item[1]["overall"], reverse=True))
        payload = {
            "schema_version": 3,
            "formula": {
                "recent_production_weight": RECENT_WEIGHT,
                "department_weight": DEPARTMENT_WEIGHT,
                "rank_weight": RANK_WEIGHT,
                "long_history_weight": HISTORY_WEIGHT,
                "recent_metric": "goals_per_game_relative_to_same_season_serie_a_average",
                "defense_metric": "inverse_goals_conceded_per_game_relative_to_same_season_serie_a_average",
            },
            "teams": teams,
        }
        with open(self.output_file, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
        print(f"Team strength aggiornato: {self.output_file}")

    def run(self) -> dict[str, Any]:
        historical = self.load_json(self.historical_file)
        departments = self.load_json(self.department_strength_file)
        result = self.merge_strengths(historical, departments)
        self.save_to_json(result)
        return result


if __name__ == "__main__":
    UnifiedTeamStrengthCalculator().run()
