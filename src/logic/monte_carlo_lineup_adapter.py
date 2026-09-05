"""Adattatore: la Monte Carlo delega la selezione pre-match al LineupService."""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

import pandas as pd

from src.data.league_config import LeagueConfig
from web.backend.services.lineup_service import LineupService


class MonteCarloLineupAdapter:
    """Converte il formato della rosa Monte Carlo nel contratto del LineupService.

    Non calcola expected score, fixture, disponibilità o selection score: sono
    prodotti esclusivamente dal servizio deterministico.
    """

    def __init__(self, settings: Any, league_config: LeagueConfig | None = None, service_factory: Callable[[pd.DataFrame], LineupService] | None = None):
        self.settings = settings
        self.league_config = league_config or LeagueConfig()
        self.service_factory = service_factory or (lambda dataframe: LineupService(dataframe, self.league_config))

    def _options(self) -> Dict[str, float]:
        return {
            "goal_bonus": self.settings.goal_bonus,
            "assist_bonus": self.settings.assist_bonus,
            "clean_sheet_bonus": self.settings.clean_sheet_bonus,
        }

    @staticmethod
    def _player(item: Dict[str, Any]) -> Dict[str, Any] | None:
        player = item.get("player") if isinstance(item, dict) else None
        player = player if isinstance(player, dict) else item
        return player if isinstance(player, dict) and player.get("id") is not None else None

    def recommend(self, roster: Iterable[Dict[str, Any]], matchday: int, formation: str) -> Dict[str, Any]:
        players = [player for item in roster if (player := self._player(item)) is not None]
        dataframe = pd.DataFrame([{
            "Id": player.get("id"),
            "Nome": player.get("nome", player.get("name", "")),
            "Squadra": player.get("squadra", ""),
            "R": player.get("ruolo", ""),
            "Overall": player.get("overall", 50),
            "Fm_weighted": player.get("fm_weighted", player.get("mv_weighted", 6.0)),
            "Mv_weighted": player.get("mv_weighted", 6.0),
            "Pv_weighted": player.get("pv_weighted", 0),
            "Gf_weighted": player.get("gf_weighted", 0),
            "Ass_weighted": player.get("ass_weighted", 0),
        } for player in players])
        service = self.service_factory(dataframe)
        lineup_roster = {"roster": [{"player": {"id": player["id"]}} for player in players]}
        if formation == "auto":
            candidates = [
                service.recommend_for_matchday(matchday, candidate, lineup_roster, self._options())
                for candidate in service.formations
            ]
            complete = [item for item in candidates if len(item["selection"]["starters"]) == 11]
            return max(complete or candidates, key=lambda item: item["lineup_summary"]["expected_score"])
        return service.recommend_for_matchday(matchday, formation, lineup_roster, self._options())
