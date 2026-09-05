"""Validazione statistica del generatore di rose avversarie.

Il modulo non modifica il comportamento della simulazione: esegue batch separati
con seed controllato e produce metriche descrittive per verificare che il draft
budget-aware non generi rose patologiche.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List

import numpy as np

from src.data.league_config import LeagueConfig
from src.logic.opponent_snake_draft import BudgetAwareSnakeDraft


@dataclass(frozen=True)
class DistributionSummary:
    minimum: float
    p25: float
    median: float
    p75: float
    maximum: float
    mean: float
    std: float


@dataclass(frozen=True)
class BatchValidationReport:
    iterations: int
    teams_per_iteration: int
    roster_size: int
    budget_distribution: DistributionSummary
    spent_distribution: DistributionSummary
    surplus_distribution: DistributionSummary
    theoretical_value_distribution: DistributionSummary
    top11_quality_distribution: DistributionSummary
    bench_quality_distribution: DistributionSummary
    concentration_top11_distribution: DistributionSummary
    invariant_failures: int
    duplicate_failures: int
    completion_failures: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OpponentDraftValidator:
    """Esegue controlli statistici senza introdurre soglie economiche hardcoded."""

    def __init__(self, config: LeagueConfig):
        self.config = config
        self.roster_size = sum(config.roster_composition.values())

    @staticmethod
    def _summary(values: Iterable[float]) -> DistributionSummary:
        arr = np.asarray(list(values), dtype=float)
        if arr.size == 0:
            return DistributionSummary(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        q = np.quantile(arr, [0.0, 0.25, 0.5, 0.75, 1.0])
        return DistributionSummary(
            minimum=float(q[0]),
            p25=float(q[1]),
            median=float(q[2]),
            p75=float(q[3]),
            maximum=float(q[4]),
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
        )

    @staticmethod
    def _quality(player: Dict[str, Any]) -> float:
        for key in ("fm_weighted", "overall", "mv_weighted"):
            try:
                value = float(player.get(key, 0) or 0)
                if np.isfinite(value):
                    return value
            except (TypeError, ValueError):
                pass
        return 0.0

    def run(
        self,
        players: Iterable[Dict[str, Any]],
        teams: List[str],
        iterations: int = 100,
        seed: int = 1,
    ) -> BatchValidationReport:
        players = [dict(p) for p in players]
        if iterations <= 0:
            raise ValueError("iterations deve essere > 0")
        if not teams:
            raise ValueError("teams non può essere vuoto")

        rng = np.random.default_rng(seed)
        budget_remaining: List[float] = []
        spent: List[float] = []
        surplus: List[float] = []
        theoretical_value: List[float] = []
        top11_quality: List[float] = []
        bench_quality: List[float] = []
        concentration_top11: List[float] = []
        invariant_failures = duplicate_failures = completion_failures = 0

        expected_roles = self.config.roster_composition
        top11_size = min(11, self.roster_size)

        for _ in range(iterations):
            draft = BudgetAwareSnakeDraft(self.config, rng)
            try:
                rosters = draft.draft(players, teams)
            except ValueError:
                completion_failures += 1
                continue

            seen_ids = set()
            for team in teams:
                roster = rosters.get(team, [])
                ids = [p.get("id") for p in roster]
                if any(pid in seen_ids for pid in ids):
                    duplicate_failures += 1
                seen_ids.update(ids)

                role_counts = {role: 0 for role in expected_roles}
                for player in roster:
                    role = str(player.get("ruolo", "")).strip()[:1].upper()
                    if role in role_counts:
                        role_counts[role] += 1

                valid = (
                    len(roster) == self.roster_size
                    and role_counts == expected_roles
                )
                prices = [float(p.get("simulated_price", 0.0) or 0.0) for p in roster]
                spent_team = float(sum(prices))
                remaining_team = float(self.config.starting_budget - spent_team)
                if not valid or spent_team > self.config.starting_budget + 1e-9 or remaining_team < self.config.reserve - 1e-9:
                    invariant_failures += 1

                values = [float(p.get("theoretical_value", 0.0) or 0.0) for p in roster]
                qualities = sorted((self._quality(p) for p in roster), reverse=True)
                top11 = qualities[:top11_size]
                bench = qualities[top11_size:]

                budget_remaining.append(remaining_team)
                spent.append(spent_team)
                surplus.append(float(sum(values) - spent_team))
                theoretical_value.append(float(sum(values)))
                top11_quality.append(float(np.mean(top11)) if top11 else 0.0)
                bench_quality.append(float(np.mean(bench)) if bench else 0.0)
                ranked_by_quality = sorted(roster, key=self._quality, reverse=True)[:top11_size]
                top11_ids = {player.get("id") for player in ranked_by_quality}
                premium_spend = sum(
                    float(player.get("simulated_price", 0.0) or 0.0)
                    for player in roster
                    if player.get("id") in top11_ids
                )
                concentration_top11.append(premium_spend / spent_team if spent_team > 0 else 0.0)

        return BatchValidationReport(
            iterations=iterations,
            teams_per_iteration=len(teams),
            roster_size=self.roster_size,
            budget_distribution=self._summary(budget_remaining),
            spent_distribution=self._summary(spent),
            surplus_distribution=self._summary(surplus),
            theoretical_value_distribution=self._summary(theoretical_value),
            top11_quality_distribution=self._summary(top11_quality),
            bench_quality_distribution=self._summary(bench_quality),
            concentration_top11_distribution=self._summary(concentration_top11),
            invariant_failures=invariant_failures,
            duplicate_failures=duplicate_failures,
            completion_failures=completion_failures,
        )
