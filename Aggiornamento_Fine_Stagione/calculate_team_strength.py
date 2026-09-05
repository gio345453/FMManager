"""Genera componenti storiche di forza squadra da dati Serie A comparabili."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


HISTORY_WEIGHTS = (0.60, 0.25, 0.15)
SERIE_A = "serie a"


class TeamStrengthCalculator:
    """Calcola produzione recente e storico lungo su scala 1-10."""

    def __init__(
        self,
        stats_file: str = "Aggiornamento_Fine_Stagione/team_stats_fbref.json",
        standings_file: str = "data/Calendario/season_standings.json",
        output_file: str = "data/Calendario/team_historical_strength.json",
    ):
        self.stats_file = Path(stats_file)
        self.standings_file = Path(standings_file)
        self.output_file = Path(output_file)

    @staticmethod
    def _season_sort_key(season: str) -> tuple[int, str]:
        try:
            return int(str(season).split("-")[0]), str(season)
        except (TypeError, ValueError):
            return 0, str(season)

    @staticmethod
    def _scale(values: Mapping[str, float]) -> dict[str, float]:
        if not values:
            return {}
        low, high = min(values.values()), max(values.values())
        if high == low:
            return {team: 5.5 for team in values}
        return {
            team: round(1.0 + 9.0 * (value - low) / (high - low), 3)
            for team, value in values.items()
        }

    def load_stats(self) -> dict[str, Any]:
        with open(self.stats_file, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_standings(self) -> dict[str, Any]:
        if not self.standings_file.exists():
            return {}
        with open(self.standings_file, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _valid_number(value: Any) -> float | None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if number >= 0 else None

    def _season_is_serie_a(self, season: str, teams: Mapping[str, Any], metadata: Mapping[str, Any]) -> bool:
        declared = metadata.get("league")
        if declared is not None:
            return str(declared).strip().lower() == SERIE_A
        return len(teams) == 20

    def _build_season_ratings(
        self,
        season: str,
        teams: Mapping[str, Any],
        metadata: Mapping[str, Any],
        source_quality: str,
    ) -> dict[str, Any] | None:
        if not self._season_is_serie_a(season, teams, metadata):
            return None

        rows: dict[str, dict[str, float]] = {}
        for team, raw in teams.items():
            if not isinstance(raw, Mapping):
                continue
            gf = self._valid_number(raw.get("gf"))
            gs = self._valid_number(raw.get("gs"))
            played = self._valid_number(raw.get("partite", raw.get("matches")))
            if gf is None or gs is None or played is None or played <= 0:
                continue
            rows[str(team)] = {"gf_per_game": gf / played, "gs_per_game": gs / played}

        if len(rows) < 2:
            return None

        league_gf = sum(row["gf_per_game"] for row in rows.values()) / len(rows)
        league_gs = sum(row["gs_per_game"] for row in rows.values()) / len(rows)
        if league_gf <= 0 or league_gs <= 0:
            return None

        attack_ratio = {team: row["gf_per_game"] / league_gf for team, row in rows.items()}
        defense_ratio = {team: league_gs / row["gs_per_game"] if row["gs_per_game"] else 0.0 for team, row in rows.items()}
        attack = self._scale(attack_ratio)
        defense = self._scale(defense_ratio)
        return {
            "season": season,
            "league": "Serie A",
            "source_quality": source_quality,
            "league_gf_per_game": round(league_gf, 4),
            "league_gs_per_game": round(league_gs, 4),
            "teams": {
                team: {
                    "attack": attack[team],
                    "defense": defense[team],
                    "gf_per_game": round(row["gf_per_game"], 4),
                    "gs_per_game": round(row["gs_per_game"], 4),
                    "attack_ratio": round(attack_ratio[team], 4),
                    "defense_ratio": round(defense_ratio[team], 4),
                }
                for team, row in rows.items()
            },
        }

    def build_season_ratings(self, stats_data: Mapping[str, Any], standings_data: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        metadata = stats_data.get("_meta", {}) if isinstance(stats_data, Mapping) else {}
        metadata_seasons = metadata.get("seasons", {}) if isinstance(metadata, Mapping) else {}
        ratings: list[dict[str, Any]] = []

        for season, teams in stats_data.items():
            if season == "_meta" or not isinstance(teams, Mapping):
                continue
            season_metadata = metadata_seasons.get(season, {}) if isinstance(metadata_seasons, Mapping) else {}
            rating = self._build_season_ratings(season, teams, season_metadata, "complete" if season_metadata else "legacy_serie_a")
            if rating:
                ratings.append(rating)

        if isinstance(standings_data, Mapping):
            season = standings_data.get("season")
            league = str(standings_data.get("league", "")).strip().lower()
            teams = standings_data.get("teams")
            if season and league == SERIE_A and isinstance(teams, Mapping):
                participants = len(teams)
                matches = max(1, participants * 2 - 2)
                rows = {
                    team: {**values, "partite": values.get("partite", matches)}
                    for team, values in teams.items()
                    if isinstance(values, Mapping)
                }
                rating = self._build_season_ratings(
                    str(season),
                    rows,
                    {"league": "Serie A"},
                    "season_standings",
                )
                if rating:
                    ratings = [item for item in ratings if item["season"] != season]
                    ratings.append(rating)

        return sorted(ratings, key=lambda item: self._season_sort_key(item["season"]), reverse=True)

    @staticmethod
    def _weighted_component(values: list[tuple[str, float]]) -> tuple[float | None, list[dict[str, float | str]]]:
        if not values:
            return None, []
        nominal = HISTORY_WEIGHTS[: len(values)]
        denominator = sum(nominal)
        effective = [weight / denominator for weight in nominal]
        score = sum(value * weight for (_, value), weight in zip(values, effective))
        return round(score, 3), [
            {"season": season, "weight": round(weight, 4)}
            for (season, _), weight in zip(values, effective)
        ]

    def calculate_components(self, stats_data: Mapping[str, Any], standings_data: Mapping[str, Any] | None = None) -> dict[str, Any]:
        ratings = self.build_season_ratings(stats_data, standings_data)
        if not ratings:
            return {"schema_version": 1, "formula": {"history_weights": list(HISTORY_WEIGHTS)}, "teams": {}}

        latest = ratings[0]
        team_names = sorted({team for rating in ratings for team in rating["teams"]})
        teams: dict[str, dict[str, Any]] = {}
        for team in team_names:
            recent = latest["teams"].get(team)
            history_attack = [(rating["season"], rating["teams"][team]["attack"]) for rating in ratings[1:] if team in rating["teams"]][:3]
            history_defense = [(rating["season"], rating["teams"][team]["defense"]) for rating in ratings[1:] if team in rating["teams"]][:3]
            historical_attack, attack_weights = self._weighted_component(history_attack)
            historical_defense, defense_weights = self._weighted_component(history_defense)
            teams[team] = {
                "recent_attack": recent["attack"] if recent else None,
                "recent_defense": recent["defense"] if recent else None,
                "historical_attack": historical_attack,
                "historical_defense": historical_defense,
                "recent_season": latest["season"] if recent else None,
                "recent_source_quality": latest["source_quality"] if recent else "missing",
                "historical_attack_weights": attack_weights,
                "historical_defense_weights": defense_weights,
            }
            if recent:
                teams[team].update({
                    "recent_gf_per_game": recent["gf_per_game"],
                    "recent_gs_per_game": recent["gs_per_game"],
                    "recent_attack_ratio": recent["attack_ratio"],
                    "recent_defense_ratio": recent["defense_ratio"],
                })

        return {
            "schema_version": 1,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "formula": {
                "recent_metric": "team_goals_per_game / league_goals_per_game",
                "defense_metric": "league_goals_conceded_per_game / team_goals_conceded_per_game",
                "history_weights": list(HISTORY_WEIGHTS),
                "recent_season": latest["season"],
            },
            "seasons": [
                {
                    key: rating[key]
                    for key in ("season", "league", "source_quality", "league_gf_per_game", "league_gs_per_game")
                }
                for rating in ratings
            ],
            "teams": teams,
        }

    def save_team_strength(self, components: Mapping[str, Any]) -> None:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as file:
            json.dump(components, file, indent=2, ensure_ascii=False)
        print(f"Componenti storiche salvate: {self.output_file}")

    def run(self) -> dict[str, Any]:
        components = self.calculate_components(self.load_stats(), self.load_standings())
        self.save_team_strength(components)
        return components


if __name__ == "__main__":
    TeamStrengthCalculator().run()
