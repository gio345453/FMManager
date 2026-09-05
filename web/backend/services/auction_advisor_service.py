"""Auction Advisor evoluto e data-driven.

Principi:
- il valore economico di base arriva dal PriceCalculator esistente;
- il valore sportivo resta separato dal prezzo;
- la decisione dipende dal valore marginale della rosa, non dal valore assoluto;
- il budget è un vincolo strategico, non una penalità arbitraria dello score;
- tier, status, alternative, mercato, calendario, complementarità e rischio
  confluiscono nel controfattuale della rosa;
- tutti i parametri di lega sono letti da state/rules; nessuna regola di asta
  viene duplicata nel codice.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from src.data.titolarita_loader import load_status_map
try:
    from src.data.fixture_difficulty import get_fixture_calculator
except Exception:  # pragma: no cover
    get_fixture_calculator = None

try:
    from src.data.goalkeeper_rotation import get_rotation_analyzer
except Exception:  # pragma: no cover - fallback se il modulo non e' disponibile
    get_rotation_analyzer = None

ROLES = ("P", "D", "C", "A")
TIER_LABELS = ("ELITE", "PREMIUM", "FORTE", "STANDARD", "DEPTH")


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    return int(round(_float(value, default)))


def _base_role(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text.split("/")[0].split("(")[0].strip()


def _normalized_name(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _round_bid(value: float, minimum: float, increment: float) -> int:
    if value < minimum:
        return 0
    step = max(1, int(round(increment)))
    base = max(0, int(math.ceil(minimum)))
    if base == 0:
        return int(math.floor(value / step) * step)
    return base + max(0, int(math.floor((value - base) / step))) * step


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AdvisorConfig:
    """Configurazione opzionale dell'Advisor.

    Le regole di lega arrivano sempre da state/rules. Questi campi permettono
    di tarare solamente aspetti numerici del modello senza modificare il codice.
    Se assenti, l'Advisor usa formule adattive derivate dai dati disponibili.
    """

    beam_width: Optional[int] = None
    max_role_candidates: Optional[int] = None
    exact_search_limit: Optional[int] = None
    market_prior_strength: Optional[float] = None
    local_verification_steps: Optional[int] = None

    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "AdvisorConfig":
        rules = state.get("rules") or {}
        raw = state.get("advisor_config")
        if not isinstance(raw, dict):
            raw = rules.get("advisor_config")
        if not isinstance(raw, dict):
            raw = {}

        def optional_int(name: str) -> Optional[int]:
            value = raw.get(name)
            if value is None:
                return None
            parsed = _int(value, 0)
            return parsed if parsed > 0 else None

        def optional_float(name: str) -> Optional[float]:
            value = raw.get(name)
            if value is None:
                return None
            parsed = _float(value, 0.0)
            return parsed if parsed > 0 else None

        return cls(
            beam_width=optional_int("beam_width"),
            max_role_candidates=optional_int("max_role_candidates"),
            exact_search_limit=optional_int("exact_search_limit"),
            market_prior_strength=optional_float("market_prior_strength"),
            local_verification_steps=optional_int("local_verification_steps"),
        )


class AuctionAdvisorService:
    """Motore decisionale dell'asta."""

    def __init__(self, players_df: pd.DataFrame, price_calculator):
        self.players_df = players_df if players_df is not None else pd.DataFrame()
        self.price_calculator = price_calculator
        self._data_revision = self._compute_data_revision()
        self._player_cache: Dict[Tuple[str, int, float], Dict[str, Any]] = {}
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self._frontier_cache: Dict[str, Dict[str, Any]] = {}
        self._forced_plan_cache: Dict[str, Dict[str, Any]] = {}
        self._rotation_cache: Dict[str, Dict[str, Any]] = {}
        self._alternative_cache: Dict[str, Dict[str, Any]] = {}
        self._fixture_profile_cache: Dict[str, Dict[str, Any]] = {}
        try:
            self.status_map = load_status_map()
        except Exception:
            self.status_map = {}

    def _compute_data_revision(self) -> str:
        if self.players_df is None or self.players_df.empty:
            return "empty"
        sample = self.players_df.copy()
        columns = [c for c in ("Id", "Nome", "Squadra", "R", "Overall", "Fm_weighted", "Mv_weighted", "Pv_weighted", "Titolarita") if c in sample.columns]
        if columns:
            sample = sample[columns].sort_values(columns[0]).reset_index(drop=True)
        return _stable_hash({
            "shape": sample.shape,
            "columns": list(sample.columns),
            "head": sample.head(3).to_dict("records"),
            "tail": sample.tail(3).to_dict("records"),
        })

    def update_players(self, players_df: pd.DataFrame, price_calculator=None) -> None:
        self.players_df = players_df if players_df is not None else pd.DataFrame()
        if price_calculator is not None:
            self.price_calculator = price_calculator
        self._data_revision = self._compute_data_revision()
        self._player_cache.clear()
        self._context_cache.clear()
        self._frontier_cache.clear()
        self._forced_plan_cache.clear()
        self._rotation_cache.clear()
        self._alternative_cache.clear()
        self._fixture_profile_cache.clear()
        try:
            self.status_map = load_status_map()
        except Exception:
            pass

    def _row(self, player_id: int):
        if self.players_df is None or self.players_df.empty or "Id" not in self.players_df.columns:
            return None
        rows = self.players_df[self.players_df["Id"] == int(player_id)]
        return rows.iloc[0] if not rows.empty else None

    @staticmethod
    def _status_category(raw_status: Any) -> str:
        low = _normalized_name(raw_status)
        if not low:
            return "UNKNOWN"
        # Solo classificazione semantica di fallback; i pesi non sono codificati qui.
        aliases = (
            ("INJURED", ("infortun", "injur", "lesionat", "fuori per")),
            ("SUSPENDED", ("squalif", "sospes")),
            ("DOUBTFUL", ("ballott", "dubbio", "incert")),
            ("BENCH", ("panch", "riserva", "bench")),
            ("ROTATION", ("rotation", "rotazione")),
            ("STARTER", ("titolare", "starter")),
            ("AVAILABLE", ("disponibile", "available")),
        )
        for category, words in aliases:
            if any(word in low for word in words):
                return category
        return "UNKNOWN"

    def _status_reference(self, players: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        groups: Dict[str, List[float]] = {}
        for player in players:
            category = self._status_category(player.get("status"))
            if category == "UNKNOWN":
                continue
            historical = _float(player.get("titolarita"), 0.0) / 100.0
            if historical <= 0:
                matchdays = _int(player.get("matchdays"), 0)
                if matchdays > 0:
                    historical = min(1.0, _float(player.get("pv")) / matchdays)
            if historical > 0:
                groups.setdefault(category, []).append(max(0.0, min(1.0, historical)))
        return {
            category: {
                "median": median(values),
                "count": float(len(values)),
            }
            for category, values in groups.items()
            if values
        }

    def _status_profile(
        self,
        player: Dict[str, Any],
        status_reference: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        raw = str(player.get("status") or "").strip()
        category = self._status_category(raw)
        reference = (status_reference or {}).get(category, {})
        tit = _float(player.get("titolarita"), 0.0) / 100.0
        matchdays = _int(player.get("matchdays"), 0)
        pv_availability = min(1.0, _float(player.get("pv"), 0.0) / matchdays) if matchdays > 0 else 0.0

        empirical_values = []
        if tit > 0:
            empirical_values.append(max(0.0, min(1.0, tit)))
        if pv_availability > 0:
            empirical_values.append(max(0.0, min(1.0, pv_availability)))
        if reference.get("median", 0) > 0:
            empirical_values.append(reference["median"])

        availability = median(empirical_values) if empirical_values else 0.0
        if category == "UNKNOWN" and availability <= 0:
            availability = 1.0 if player.get("status") else 0.0

        risk = max(0.0, min(1.0, 1.0 - availability))
        reasons: List[str] = []
        if raw:
            reasons.append(f"Status: {raw} ({category}).")
        if tit > 0:
            reasons.append(f"Titolarità stimata {tit * 100:.0f}%.")

        source_quality = 0.0
        if raw:
            source_quality = 1.0 if category != "UNKNOWN" else 0.5
        elif tit > 0 or pv_availability > 0:
            source_quality = 0.5

        return {
            "raw": raw or "N/D",
            "category": category,
            "availability": availability,
            "risk": risk,
            "sourceQuality": source_quality,
            "reasons": reasons,
        }

    def _player(self, player_id: int, budget: float, matchdays: Optional[int] = None) -> Optional[Dict[str, Any]]:
        matchday_key = _int(matchdays, 0)
        cache_key = (self._data_revision, int(player_id), round(float(budget), 2))
        cached = self._player_cache.get(cache_key)
        if cached is not None:
            player = dict(cached)
            if matchday_key:
                player["matchdays"] = matchday_key
            return player

        row = self._row(player_id)
        if row is None or self.price_calculator is None:
            return None
        try:
            price = self.price_calculator.calculate_price_percentage(int(player_id), budget)
        except Exception:
            return None

        name = str(row.get("Nome", ""))
        status = self.status_map.get(name, row.get("status", None))
        player = {
            "id": int(player_id),
            "nome": name,
            "squadra": str(row.get("Squadra", "")),
            "ruolo_raw": str(row.get("R", "")),
            "ruolo": _base_role(row.get("R")),
            "overall": _int(row.get("Overall")),
            "fm": _float(row.get("Fm_weighted")),
            "mv": _float(row.get("Mv_weighted")),
            "pv": _float(row.get("Pv_weighted")),
            "gf": _float(row.get("Gf_weighted")),
            "ass": _float(row.get("Ass_weighted")),
            "titolarita": _float(row.get("Titolarita")),
            "status": status,
            "price_percentage": _float(price.get("percentage")),
            "price_credits": _float(price.get("credits")),
        }
        if matchday_key:
            player["matchdays"] = matchday_key
        self._player_cache[cache_key] = dict(player)
        return player

    @staticmethod
    def _role_need(team: Dict[str, Any], role: str, composition: Dict[str, int]) -> int:
        owned = sum(1 for item in (team.get("roster") or []) if _base_role(item.get("role")) == role)
        return max(0, int(composition.get(role, 0)) - owned)

    @classmethod
    def _needs(cls, team: Dict[str, Any], composition: Dict[str, int]) -> Dict[str, int]:
        return {role: cls._role_need(team, role, composition) for role in ROLES}

    def _enrich_existing_roster(
        self,
        roster: Sequence[Dict[str, Any]],
        budget: float,
        matchdays: int,
    ) -> List[Dict[str, Any]]:
        enriched: List[Dict[str, Any]] = []
        for item in roster:
            if not isinstance(item, dict):
                continue
            pid = _int(item.get("player_id"), _int(item.get("id"), 0))
            player = self._player(pid, budget, matchdays) if pid > 0 else None
            if player is None:
                # Mantiene comunque le informazioni minime presenti nello stato asta.
                player = {
                    "id": pid,
                    "nome": str(item.get("name") or ""),
                    "squadra": str(item.get("team") or ""),
                    "ruolo": _base_role(item.get("role")),
                    "overall": _int(item.get("overall"), 0),
                    "fm": _float(item.get("fm"), 0.0),
                    "mv": _float(item.get("mv"), 0.0),
                    "pv": _float(item.get("pv"), 0.0),
                    "gf": _float(item.get("gf"), 0.0),
                    "ass": _float(item.get("ass"), 0.0),
                    "titolarita": _float(item.get("titolarita"), 0.0),
                    "status": item.get("status"),
                    "price_percentage": _float(item.get("price_percentage"), 0.0),
                    "price_credits": _float(item.get("price"), 0.0),
                }
            else:
                player = dict(player)
            player["price_credits"] = _float(item.get("price"), _float(player.get("price_credits"), 0.0))
            if item.get("status") is not None:
                player["status"] = item.get("status")
            enriched.append(player)
        status_reference = self._status_reference(enriched)
        for player in enriched:
            profile = self._status_profile(player, status_reference)
            player["status_category"] = profile["category"]
            player["availability"] = profile["availability"]
            player["status_risk"] = profile["risk"]
            player["status_source_quality"] = profile["sourceQuality"]
        return enriched

    @staticmethod
    def _roster_signature(team: Dict[str, Any]) -> List[Tuple[int, float, str, str]]:
        signature = []
        for item in team.get("roster") or []:
            signature.append((
                _int(item.get("player_id"), _int(item.get("id"))),
                _float(item.get("price")),
                str(item.get("role") or ""),
                str(item.get("team") or ""),
            ))
        return sorted(signature)

    def _state_context_key(self, state: Dict[str, Any], team: Dict[str, Any]) -> str:
        rules = state.get("rules") or {}
        assigned = []
        for pid, assignment in sorted((state.get("assigned") or {}).items(), key=lambda x: str(x[0])):
            assigned.append((str(pid), _float((assignment or {}).get("price")), str((assignment or {}).get("owner"))))
        return _stable_hash({
            "data": self._data_revision,
            "budget": _float(rules.get("starting_credits")),
            "composition": rules.get("composition") or {},
            "min": _float(rules.get("minimum_price"), 1),
            "increment": _float(rules.get("bid_increment"), 1),
            "reserve": _float(rules.get("reserve_per_slot"), 0),
            "assigned": assigned,
            "team": {
                "id": team.get("id"),
                "credits": _float(team.get("credits")),
                "roster": self._roster_signature(team),
            },
        })

    def _all_role_players(self, budget: float, state: Dict[str, Any], matchdays: int) -> List[Dict[str, Any]]:
        if self.players_df is None or self.players_df.empty or self.price_calculator is None:
            return []
        assigned_ids = {int(pid) for pid in (state.get("assigned") or {}).keys()}
        population: List[Dict[str, Any]] = []
        for pid in self.players_df["Id"].tolist():
            player = self._player(int(pid), budget, matchdays)
            if player and player["ruolo"] in ROLES:
                population.append(player)
        status_reference = self._status_reference(population)
        for player in population:
            profile = self._status_profile(player, status_reference)
            player["status_category"] = profile["category"]
            player["availability"] = profile["availability"]
            player["status_risk"] = profile["risk"]
            player["status_source_quality"] = profile["sourceQuality"]
        # I tier sono assoluti rispetto al pool della lega, non rispetto alla squadra utente.
        self._tierize(population)
        return [p for p in population if int(p["id"]) not in assigned_ids]

    @staticmethod
    def _absolute_value(player: Dict[str, Any]) -> float:
        fm = max(0.0, _float(player.get("fm")))
        availability = max(0.0, min(1.0, _float(player.get("availability"), 1.0)))
        return fm * availability

    def _quick_expected(self, player: Dict[str, Any]) -> float:
        """Valore sportivo atteso leggero usato per ranking e presentazione.

        Rimane coerente con il layer di valore assoluto e non introduce
        moltiplicatori o soglie arbitrarie. Ridondanza, complementarita e
        altri aggiustamenti vengono applicati nei layer successivi.
        """
        return self._absolute_value(player)

    def _tierize(self, players: List[Dict[str, Any]]) -> None:
        by_role: Dict[str, List[Dict[str, Any]]] = {r: [] for r in ROLES}
        for p in players:
            by_role.setdefault(p["ruolo"], []).append(p)
        for role, pool in by_role.items():
            ordered = sorted(
                pool,
                key=lambda x: (self._absolute_value(x), _float(x.get("overall")), _float(x.get("price_percentage"))),
                reverse=True,
            )
            n = len(ordered)
            if not n:
                continue
            for index, player in enumerate(ordered):
                # Cinque fasce equiprobabili ricavate dal ranking corrente del ruolo.
                bucket = min(len(TIER_LABELS) - 1, int(index * len(TIER_LABELS) / n))
                tier = TIER_LABELS[bucket]
                player["tier"] = tier
                player["role_rank"] = index + 1
                player["role_percentile"] = round(100.0 * (n - index) / n, 1)

    @staticmethod
    def _market_ratios(records: Sequence[Dict[str, Any]]) -> List[float]:
        ratios = []
        for record in records:
            reference = _float(record.get("player", {}).get("price_credits"), 0.0)
            price = _float(record.get("price"), 0.0)
            if reference > 0 and price > 0:
                ratios.append(price / reference)
        return ratios

    @staticmethod
    def _shrink_observation(observed: float, count: int, prior: float = 1.0, strength: Optional[float] = None) -> float:
        if count <= 0:
            return prior
        prior_weight = strength if strength and strength > 0 else math.sqrt(count)
        empirical_weight = float(count)
        return (observed * empirical_weight + prior * prior_weight) / (empirical_weight + prior_weight)

    @classmethod
    def _market_model(cls, records: List[Dict[str, Any]], config: AdvisorConfig) -> Dict[str, Any]:
        all_ratios = cls._market_ratios(records)
        role_ratios = {role: [] for role in ROLES}
        for record in records:
            player = record.get("player") or {}
            role = player.get("ruolo")
            reference = _float(player.get("price_credits"), 0.0)
            price = _float(record.get("price"), 0.0)
            if role in role_ratios and reference > 0 and price > 0:
                role_ratios[role].append(price / reference)

        def robust_band(values: List[float]) -> Tuple[float, float, float]:
            if not values:
                return 1.0, 1.0, 1.0
            series = pd.Series(values, dtype=float)
            median_value = float(series.median())
            low = float(series.quantile(0.25)) if len(series) > 1 else median_value
            high = float(series.quantile(0.75)) if len(series) > 1 else median_value
            return median_value, low, high

        observed, low, high = robust_band(all_ratios)
        inflation = cls._shrink_observation(observed, len(all_ratios), 1.0, config.market_prior_strength)
        role_inflation: Dict[str, float] = {}
        role_band: Dict[str, Dict[str, float]] = {}
        for role in ROLES:
            values = role_ratios[role]
            role_observed, role_low, role_high = robust_band(values)
            if values:
                role_inflation[role] = cls._shrink_observation(role_observed, len(values), inflation, config.market_prior_strength)
                role_band[role] = {
                    "median": cls._shrink_observation(role_observed, len(values), 1.0, config.market_prior_strength),
                    "low": cls._shrink_observation(role_low, len(values), 1.0, config.market_prior_strength),
                    "high": cls._shrink_observation(role_high, len(values), 1.0, config.market_prior_strength),
                }
            else:
                role_inflation[role] = inflation
                role_band[role] = {"median": inflation, "low": inflation, "high": inflation}

        return {
            "inflation": inflation,
            "role_inflation": role_inflation,
            "role_band": role_band,
            "records": len(all_ratios),
            "confidence": 1.0 - 1.0 / (1.0 + math.sqrt(len(all_ratios))) if all_ratios else 0.0,
        }

    @classmethod
    def _scarcity(
        cls,
        remaining: List[Dict[str, Any]],
        teams: List[Dict[str, Any]],
        composition: Dict[str, int],
    ) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for role in ROLES:
            pool = [p for p in remaining if p["ruolo"] == role]
            supply = len(pool)
            demand = sum(cls._role_need(team, role, composition) for team in teams)
            values = [cls._absolute_value(p) for p in pool]
            median_value = median(values) if values else 0.0
            acceptable = [p for p in pool if cls._absolute_value(p) >= median_value and _float(p.get("status_risk"), 1.0) <= median([_float(x.get("status_risk"), 1.0) for x in pool]) if pool]
            quality_supply = len(acceptable)
            qualitative_ratio = demand / max(1, quality_supply)
            quantitative_ratio = demand / max(1, supply)
            result[role] = {
                "supply": supply,
                "demand": demand,
                "ratio": quantitative_ratio,
                "qualitativeSupply": quality_supply,
                "qualitativeRatio": qualitative_ratio,
                "tierSupply": {
                    tier: sum(1 for p in pool if p.get("tier") == tier)
                    for tier in TIER_LABELS
                },
            }
        return result

    @staticmethod
    def _role_targets(
        remaining: List[Dict[str, Any]],
        teams: List[Dict[str, Any]],
        composition: Dict[str, int],
        budget: float,
    ) -> Dict[str, float]:
        """Stima il budget di reparto per UNA squadra.

        I pesi derivano dal numero di slot della composizione e dal livello
        economico osservato nel pool; non dividiamo il budget per il numero di
        partecipanti, perché ogni squadra possiede il proprio budget integrale.
        """
        weights = {role: 0.0 for role in ROLES}
        for role in ROLES:
            slots = max(0, int(composition.get(role, 0)))
            if slots <= 0:
                continue
            values = [
                _float(p.get("price_percentage"), 0.0)
                for p in remaining
                if p["ruolo"] == role and _float(p.get("price_percentage"), 0.0) > 0
            ]
            role_level = median(values) if values else 0.0
            weights[role] = slots * role_level

        total = sum(weights.values())
        if total <= 0:
            slot_total = sum(max(0, int(composition.get(role, 0))) for role in ROLES)
            return {
                role: budget * int(composition.get(role, 0)) / max(1, slot_total)
                for role in ROLES
            }
        return {role: budget * weights[role] / total for role in ROLES}

    @staticmethod
    def _team_role_target(
        role: str,
        team: Dict[str, Any],
        composition: Dict[str, int],
        global_targets: Dict[str, float],
        teams: List[Dict[str, Any]],
    ) -> float:
        slots = max(1, int(composition.get(role, 0)))
        need = max(0, AuctionAdvisorService._role_need(team, role, composition))
        return global_targets.get(role, 0.0) * need / slots

    def _strategic_budget(
        self,
        team: Dict[str, Any],
        needs: Dict[str, int],
        composition: Dict[str, int],
        global_targets: Dict[str, float],
        teams: List[Dict[str, Any]],
        minimum: float,
        remaining: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        credits = max(0.0, _float(team.get("credits")))
        role_targets = {
            role: self._team_role_target(role, team, composition, global_targets, teams)
            for role in ROLES
        }
        role_minimums: Dict[str, float] = {}
        for role in ROLES:
            count = needs.get(role, 0)
            costs = sorted(
                max(minimum, _float(p.get("price_credits"), minimum))
                for p in remaining
                if p["ruolo"] == role
            )
            role_minimums[role] = sum(costs[:count]) if len(costs) >= count else float("inf")

        target_sum = sum(role_targets.get(role, 0.0) for role, count in needs.items() if count > 0)
        minimum_sum = sum(v for v in role_minimums.values() if math.isfinite(v))
        if any(count > 0 and not math.isfinite(role_minimums.get(role, float("inf"))) for role, count in needs.items()):
            return {
                "budget": min(credits, target_sum if target_sum > 0 else credits),
                "futureReserve": max(0.0, credits - min(credits, target_sum if target_sum > 0 else credits)),
                "roleTargets": role_targets,
                "roleMinimums": role_minimums,
            }

        strategic = min(credits, max(minimum_sum, target_sum)) if target_sum > 0 else min(credits, max(minimum_sum, 0.0))
        # Se i target teorici sono inferiori al minimo necessario, il budget strategico
        # sale al minimo di completamento. Non viene mai inventato oltre i crediti reali.
        strategic = min(credits, strategic)
        return {
            "budget": strategic,
            "futureReserve": max(0.0, credits - strategic),
            "roleTargets": role_targets,
            "roleMinimums": role_minimums,
        }

    def _marginal_gain_presentation(
        self,
        player: Dict[str, Any],
        role_pool: Sequence[Dict[str, Any]],
        baseline_utility: float,
        current_utility_delta: float,
    ) -> Dict[str, Any]:
        """Traduce il delta tecnico in una metrica leggibile e normalizzata.

        La percentuale misura quanto la rosa migliora rispetto alla baseline
        senza il candidato, mentre il livello viene ricavato dalla distribuzione
        dei delta del ruolo corrente: nessuna soglia numerica rigida.
        """
        denominator = max(abs(_float(baseline_utility)), 1e-9)
        gain_pct = (_float(current_utility_delta) / denominator) * 100.0

        role_gains: List[float] = []
        for candidate in role_pool:
            candidate_value = self._absolute_value(candidate)
            if candidate_value <= 0:
                continue
            # Stima coerente e veloce del contributo relativo prima del prezzo:
            # valore atteso rispetto al profilo piu' debole dello stesso ruolo.
            role_gains.append(self._quick_expected(candidate))

        if role_gains:
            ordered = sorted(role_gains)
            rank = sum(value <= self._quick_expected(player) for value in ordered) / len(ordered)
        else:
            rank = 0.5

        # Etichette determinate dalla posizione relativa, non da magic numbers.
        if gain_pct <= 0:
            level = "NULLO"
            label = "Nessun vantaggio rispetto alla migliore alternativa"
        elif rank >= 0.95:
            level = "ECCEZIONALE"
            label = "Vantaggio eccezionale sulla migliore alternativa"
        elif rank >= 0.80:
            level = "FORTE"
            label = "Forte vantaggio sulla migliore alternativa"
        elif rank >= 0.50:
            level = "MEDIO"
            label = "Vantaggio moderato sulla migliore alternativa"
        else:
            level = "BASSO"
            label = "Vantaggio ridotto sulla migliore alternativa"

        return {
            "percentage": round(gain_pct, 1),
            "level": level,
            "label": label,
            "direction": "POSITIVE" if gain_pct > 0 else "NON_POSITIVE",
        }

    def _purpose(self, player: Dict[str, Any], team: Dict[str, Any], needs: Dict[str, int], rotation: Optional[Dict[str, Any]] = None) -> str:
        role = player["ruolo"]
        roster = team.get("roster") or []
        if needs.get(role, 0) <= 0:
            return "NO_FIT"
        same_role = [item for item in roster if _base_role(item.get("role")) == role]
        if role == "P" and rotation:
            if rotation.get("sameTeamHandcuff"):
                return "HANDCUFF"
            if rotation.get("rotationDelta", 0.0) > 0:
                return "HANDCUFF_STRATEGICO"
        if not same_role:
            return "STARTER"
        return "COVERAGE"

    def _redundancy_profile(self, player: Dict[str, Any], team: Dict[str, Any], composition: Dict[str, int]) -> Dict[str, float]:
        role = player["ruolo"]
        owned = [item for item in team.get("roster") or [] if _base_role(item.get("ruolo", item.get("role"))) == role]
        if not owned:
            return {"penalty": 0.0, "similarity": 0.0, "coverage": 0.0}

        player_rank = _int(player.get("role_rank"), 1)
        # In assenza del rank salvato nel roster, usa la vicinanza tra tier se presente.
        similarities = []
        owned_tiers = []
        for item in owned:
            owned_tiers.append(str(item.get("tier") or ""))
            owned_rank = _int(item.get("role_rank"), 0)
            if owned_rank > 0 and player_rank > 0:
                similarities.append(1.0 / (1.0 + abs(player_rank - owned_rank)))
            elif item.get("tier") and player.get("tier"):
                similarities.append(1.0 if item.get("tier") == player.get("tier") else 0.0)
            else:
                owned_value = self._absolute_value(item)
                candidate_value = self._absolute_value(player)
                scale = max(owned_value, candidate_value, 1e-9)
                if owned_value > 0 and candidate_value > 0:
                    similarities.append(1.0 / (1.0 + abs(candidate_value - owned_value) / scale))
        similarity = max(similarities, default=0.0)
        slots = max(1, int(composition.get(role, 0)))
        coverage = min(1.0, len(owned) / slots)
        penalty = _float(player.get("absolute_value"), self._absolute_value(player)) * similarity * coverage
        return {"penalty": penalty, "similarity": similarity, "coverage": coverage}

    def _fixture_profile(self, team: str, role: str, current_matchday: Optional[int]) -> Dict[str, Any]:
        """Profilo calendario cacheabile per una squadra e un ruolo."""
        normalized_team = _normalized_name(team)
        from_md = max(1, _int(current_matchday, 1))
        key = _stable_hash({"team": normalized_team, "role": role, "from": from_md})
        cached = self._fixture_profile_cache.get(key)
        if cached is not None:
            return dict(cached)
        if not normalized_team or get_fixture_calculator is None:
            result = {"available": False, "score": 5.0, "easyRate": 0.0, "hardRate": 0.0, "avgDifficulty": None, "difficulties": {}}
            self._fixture_profile_cache[key] = dict(result)
            return result
        try:
            calc = get_fixture_calculator()
            difficulties: Dict[int, float] = {}
            for matchday in range(from_md, 39):
                fixture = calc.get_fixture_for_team(team, matchday)
                if not fixture:
                    continue
                modifiers = calc.calculate_difficulty_modifiers(team, matchday, role)
                difficulties[matchday] = _float((modifiers or {}).get("difficulty_score"), 5.0)
            values = list(difficulties.values())
            if not values:
                result = {"available": False, "score": 5.0, "easyRate": 0.0, "hardRate": 0.0, "avgDifficulty": None, "difficulties": {}}
            else:
                avg = sum(values) / len(values)
                result = {
                    "available": True,
                    "score": round(max(0.0, min(10.0, 10.0 - avg)), 3),
                    "easyRate": round(sum(1 for x in values if x < 4.5) / len(values), 3),
                    "hardRate": round(sum(1 for x in values if x > 7.0) / len(values), 3),
                    "avgDifficulty": round(avg, 3),
                    "difficulties": difficulties,
                }
        except Exception:
            result = {"available": False, "score": 5.0, "easyRate": 0.0, "hardRate": 0.0, "avgDifficulty": None, "difficulties": {}}
        self._fixture_profile_cache[key] = dict(result)
        return result

    def _rotation_analysis(self, player: Dict[str, Any], team: Dict[str, Any], current_matchday: Optional[int]) -> Dict[str, Any]:
        """Valuta la complementarita' reale del calendario dei portieri."""
        if player.get("ruolo") != "P":
            return {"available": False, "rotationDelta": 0.0, "sameTeamHandcuff": False, "score": None}
        existing = []
        for item in team.get("roster") or []:
            if _base_role(item.get("ruolo", item.get("role"))) != "P":
                continue
            club = str(item.get("squadra") or item.get("team") or "").strip()
            if club:
                existing.append(club)
        if not existing:
            return {"available": False, "rotationDelta": 0.0, "sameTeamHandcuff": False, "score": None}
        candidate_team = str(player.get("squadra") or "").strip()
        same_team = any(_normalized_name(t) == _normalized_name(candidate_team) for t in existing)
        existing_teams = list(dict.fromkeys(existing))
        all_teams = list(dict.fromkeys(existing + ([candidate_team] if candidate_team else [])))
        key = _stable_hash({"existingTeams": sorted(_normalized_name(t) for t in existing_teams), "candidateTeam": _normalized_name(candidate_team), "from": _int(current_matchday, 1)})
        cached = self._rotation_cache.get(key)
        if cached is not None:
            return dict(cached)
        profiles = {t: self._fixture_profile(t, "P", current_matchday) for t in all_teams}
        if not profiles or not any(p.get("available") for p in profiles.values()):
            result = {"available": False, "rotationDelta": 0.0, "sameTeamHandcuff": same_team, "score": None}
        else:
            from_md = max(1, _int(current_matchday, 1))
            def combo_score(team_names: Sequence[str]) -> Tuple[float, float, float]:
                chosen = []
                for md in range(from_md, 39):
                    vals = [profiles[t]["difficulties"].get(md) for t in team_names if profiles.get(t, {}).get("difficulties", {}).get(md) is not None]
                    if vals:
                        chosen.append(min(vals))
                if not chosen:
                    return 5.0, 0.0, 0.0
                avg = sum(chosen) / len(chosen)
                easy_rate = sum(1 for x in chosen if x < 4.5) / len(chosen)
                hard_rate = sum(1 for x in chosen if x > 7.0) / len(chosen)
                return max(0.0, min(10.0, 10.0 - avg)), easy_rate, hard_rate
            base_score, base_easy, base_hard = combo_score(existing_teams)
            combo_score_value, combo_easy, combo_hard = combo_score(all_teams)
            result = {
                "available": True,
                "rotationDelta": round(max(0.0, combo_score_value - base_score) / 10.0, 4),
                "sameTeamHandcuff": bool(same_team),
                "score": round(combo_score_value / 10.0, 4),
                "easyRate": round(combo_easy, 4),
                "hardRate": round(combo_hard, 4),
                "withoutScore": round(base_score / 10.0, 4),
                "withScore": round(combo_score_value / 10.0, 4),
            }
        self._rotation_cache[key] = dict(result)
        return result

    def _roster_profile(self, roster: Sequence[Dict[str, Any]], role: str) -> Dict[str, float]:
        players = [p for p in roster if _base_role(p.get("ruolo", p.get("role"))) == role]
        if not players:
            return {"goalRate": 0.0, "assistRate": 0.0, "fm": 0.0, "titolarita": 0.0}
        total_pv = sum(max(0.0, _float(p.get("pv"), 0.0)) for p in players)
        denom = max(total_pv, float(len(players)), 1.0)
        return {
            "goalRate": sum(max(0.0, _float(p.get("gf"), 0.0)) for p in players) / denom,
            "assistRate": sum(max(0.0, _float(p.get("ass"), 0.0)) for p in players) / denom,
            "fm": sum(self._absolute_value(p) for p in players) / max(1, len(players)),
            "titolarita": sum(max(0.0, _float(p.get("titolarita"), 0.0)) for p in players) / max(1, len(players)),
        }

    def _personalized_alternatives(
        self,
        state: Dict[str, Any],
        team: Dict[str, Any],
        player: Dict[str, Any],
        remaining: Sequence[Dict[str, Any]],
        existing_roster: Sequence[Dict[str, Any]],
        composition: Dict[str, int],
        role_market: float,
        minimum: float,
        increment: float,
        current_matchday: Optional[int],
    ) -> Dict[str, Any]:
        """Genera alternative personalizzate sulla rosa dell'utente.

        Il risultato contiene tutte le alternative valide per il conteggio, ma solo
        le migliori 5 per la UI. Per i portieri la priorita' e': handcuff della
        squadra gia' posseduta -> miglior rotazione -> sostituzioni equivalenti.
        Per D/C/A la priorita' passa da complementarita' del reparto, eventuale
        stack difensivo, calendario e poi sostituzione equivalente.
        """
        role = player.get("ruolo")
        key = _stable_hash({
            "state": self._state_context_key(state, team),
            "candidate": int(player.get("id", 0)),
            "role": role,
            "from": _int(current_matchday, 1),
        })
        cached = self._alternative_cache.get(key)
        if cached is not None:
            return dict(cached)

        role_pool = [
            p for p in remaining
            if p.get("ruolo") == role and int(p.get("id", 0)) != int(player.get("id", 0))
        ]
        candidate_value = self._absolute_value(player)
        tier_order = {tier: i for i, tier in enumerate(TIER_LABELS)}
        candidate_tier = tier_order.get(str(player.get("tier") or "STANDARD"), 3)
        quality_floor = candidate_value * 0.70
        selected_ids: set[int] = set()
        valid_ids: set[int] = set()
        ranked: List[Dict[str, Any]] = []

        if role == "P":
            owned_gks = [
                p for p in existing_roster
                if _base_role(p.get("ruolo", p.get("role"))) == "P"
            ]

            handcuffs: List[Tuple[float, Dict[str, Any], str]] = []
            for alt in role_pool:
                alt_team = _normalized_name(alt.get("squadra"))
                matching_owned = [
                    g for g in owned_gks
                    if _normalized_name(g.get("squadra", g.get("team"))) == alt_team
                ]
                if not matching_owned:
                    continue
                owner_priority = max(
                    self._absolute_value(g) * (1.0 + _float(g.get("status_risk"), 0.0))
                    for g in matching_owned
                )
                score = 100.0 + owner_priority + self._absolute_value(alt) * 0.25 - _float(alt.get("status_risk"), 0.0)
                handcuffs.append((score, alt, str(matching_owned[0].get("squadra", matching_owned[0].get("team")))))
            handcuffs.sort(key=lambda x: x[0], reverse=True)
            for score, alt, owner_team in handcuffs:
                valid_ids.add(int(alt["id"]))
            for score, alt, owner_team in handcuffs[:2]:
                rotation = self._rotation_analysis(alt, team, current_matchday)
                ranked.append({
                    "candidate": alt,
                    "score": score,
                    "type": "SAME_TEAM_HANDCUFF",
                    "reason": f"Handcuff di {owner_team}: completa la copertura dei portieri della tua rosa.",
                    "rotation": rotation,
                })
                selected_ids.add(int(alt["id"]))

            # Calcoliamo la qualita' di rotazione su TUTTI i portieri e usiamo una
            # soglia data-driven: quartile superiore dei punteggi positivi.
            rotation_rows = []
            for alt in role_pool:
                if int(alt["id"]) in selected_ids:
                    continue
                rotation = self._rotation_analysis(alt, team, current_matchday) if owned_gks else {"available": False}
                if not rotation.get("available"):
                    continue
                rscore = _float(rotation.get("score"), 0.0)
                if rscore > 0:
                    rotation_rows.append((rscore, alt, rotation))
            positive_scores = [x[0] for x in rotation_rows]
            rotation_threshold = float(pd.Series(positive_scores).quantile(0.75)) if positive_scores else 0.0
            for rscore, alt, rotation in rotation_rows:
                if rscore >= rotation_threshold:
                    valid_ids.add(int(alt["id"]))
                quality_ratio = self._absolute_value(alt) / max(candidate_value, 1e-9)
                strategic_score = 65.0 + 35.0 * rscore + 15.0 * _float(rotation.get("rotationDelta"), 0.0) + min(1.2, quality_ratio) * 10.0
                if rscore >= rotation_threshold and len([x for x in ranked if x["type"] == "ROTATION_PAIR"]) < 1:
                    ranked.append({
                        "candidate": alt,
                        "score": strategic_score,
                        "type": "ROTATION_PAIR",
                        "reason": f"Miglior abbinamento calendario: {rotation.get('easyRate', 0.0) * 100:.0f}% di fixture facili stimate.",
                        "rotation": rotation,
                    })
                    selected_ids.add(int(alt["id"]))

            # Sostituzioni equivalenti: non tutti i portieri del ruolo, ma solo
            # profili che restano nella stessa fascia/adiacente e sopra il floor.
            replacements = []
            for alt in role_pool:
                pid = int(alt["id"])
                value = self._absolute_value(alt)
                alt_tier = tier_order.get(str(alt.get("tier") or "DEPTH"), 4)
                if value < quality_floor or alt_tier > candidate_tier + 1:
                    continue
                quality = value * (1.0 - _float(alt.get("status_risk"), 0.0))
                gap = abs(candidate_value - value) / max(candidate_value, 1e-9)
                replacements.append((30.0 + quality + max(0.0, 20.0 * (1.0 - gap)), alt))
                valid_ids.add(pid)
            replacements.sort(key=lambda x: x[0], reverse=True)
            for score, alt in replacements:
                if len(ranked) >= 5:
                    break
                pid = int(alt["id"])
                if pid in selected_ids:
                    continue
                ranked.append({
                    "candidate": alt,
                    "score": score,
                    "type": "QUALITY_REPLACEMENT",
                    "reason": "Alternativa equivalente al giocatore chiamato per valore e affidabilita'.",
                    "rotation": None,
                })
                selected_ids.add(pid)

        else:
            owned_role = [
                p for p in existing_roster
                if _base_role(p.get("ruolo", p.get("role"))) == role
            ]
            roster_profile = self._roster_profile(existing_roster, role)
            owned_teams = {
                _normalized_name(p.get("squadra", p.get("team")))
                for p in owned_role
                if _normalized_name(p.get("squadra", p.get("team")))
            }
            candidates = []
            for alt in role_pool:
                pid = int(alt["id"])
                value = self._absolute_value(alt)
                alt_tier = tier_order.get(str(alt.get("tier") or "DEPTH"), 4)
                if value < quality_floor or alt_tier > candidate_tier + 1:
                    continue
                details = self._expected_for_portfolio(alt, existing_roster, composition, None, True)
                goal_rate = _float(alt.get("gf"), 0.0) / max(1.0, _float(alt.get("pv"), 0.0))
                assist_rate = _float(alt.get("ass"), 0.0) / max(1.0, _float(alt.get("pv"), 0.0))
                profile_gap = abs(goal_rate - roster_profile["goalRate"]) + abs(assist_rate - roster_profile["assistRate"])
                same_team = _normalized_name(alt.get("squadra")) in owned_teams if owned_teams else False
                fixture = self._fixture_profile(str(alt.get("squadra") or ""), role, current_matchday)
                fixture_bonus = max(0.0, fixture.get("score", 5.0) - 5.0) * 0.08 * value
                complement_bonus = min(0.20 * max(value, 1.0), profile_gap * 8.0)
                same_team_bonus = min(0.10 * max(value, 1.0), 0.5 * value) if same_team and role == "D" else 0.0
                strategic_score = details["marginal"] + complement_bonus + fixture_bonus + same_team_bonus - 0.05 * _float(alt.get("status_risk"), 0.0) * value
                if same_team and role == "D":
                    typ = "STACK_TEAM"
                    reason = "Complemento difensivo della stessa squadra: puo' creare uno stack, con rischio di concentrazione monitorato."
                elif complement_bonus > fixture_bonus and complement_bonus > 0:
                    typ = "COMPLEMENT_ROSTER"
                    reason = "Completa il reparto con un profilo meno ridondante rispetto a quelli gia' in rosa."
                elif fixture_bonus > 0:
                    typ = "CALENDAR_ADVANTAGE"
                    reason = "Aggiunge valore grazie a un calendario relativamente favorevole nel ruolo."
                else:
                    typ = "QUALITY_REPLACEMENT"
                    reason = "Alternativa equivalente per valore e affidabilita'."
                candidates.append({"candidate": alt, "score": strategic_score, "type": typ, "reason": reason, "rotation": None, "marginal": details["marginal"]})
                valid_ids.add(pid)
            candidates.sort(key=lambda x: (x["score"], self._absolute_value(x["candidate"])), reverse=True)
            for item in candidates:
                if len(ranked) >= 5:
                    break
                pid = int(item["candidate"]["id"])
                if pid not in selected_ids:
                    ranked.append(item)
                    selected_ids.add(pid)

        # Fallback universale: riempie gli slot mancanti con profili vicini, senza
        # trasformare il conteggio in "tutti i giocatori del ruolo".
        if len(ranked) < min(5, len(role_pool)):
            fallback = []
            for alt in role_pool:
                pid = int(alt["id"])
                if pid in selected_ids:
                    continue
                value = self._absolute_value(alt)
                if value < quality_floor:
                    continue
                gap = abs(candidate_value - value) / max(candidate_value, 1e-9)
                fallback.append((1.0 - gap, alt))
                valid_ids.add(pid)
            fallback.sort(key=lambda x: x[0], reverse=True)
            for similarity, alt in fallback:
                if len(ranked) >= 5:
                    break
                pid = int(alt["id"])
                if pid in selected_ids:
                    continue
                ranked.append({"candidate": alt, "score": 10.0 * similarity, "type": "VALUE_ALTERNATIVE", "reason": "Fallback: alternativa ancora disponibile e vicina al profilo del giocatore chiamato.", "rotation": None})
                selected_ids.add(pid)

        alternatives = []
        for item in ranked[:5]:
            alt = item["candidate"]
            rotation = item.get("rotation") or {}
            estimated = _float(alt.get("price_credits"), minimum) * role_market
            alternatives.append({
                "id": int(alt["id"]),
                "name": alt.get("nome"),
                "role": alt.get("ruolo"),
                "team": alt.get("squadra"),
                "tier": alt.get("tier"),
                "type": item["type"],
                "reason": item["reason"],
                "pricePercentage": round(_float(alt.get("price_percentage")), 1),
                "estimatedCost": _round_bid(estimated, minimum, increment),
                "valueGap": round(candidate_value - self._absolute_value(alt), 3),
                "roleRank": _int(alt.get("role_rank"), 0),
                "rotationScore": round(_float(rotation.get("score"), 0.0), 3) if rotation else None,
                "rotationDelta": round(_float(rotation.get("rotationDelta"), 0.0), 3) if rotation else None,
                "easyRate": round(_float(rotation.get("easyRate"), 0.0), 3) if rotation else None,
                "sameTeamHandcuff": bool(rotation.get("sameTeamHandcuff")) if rotation else item["type"] == "SAME_TEAM_HANDCUFF",
                "strategicScore": round(_float(item.get("score"), 0.0), 3),
            })

        result = {
            "alternatives": alternatives,
            "validAlternativesCount": int(len(valid_ids)),
            "strategy": {
                "role": role,
                "primary": "PERSONALIZED_ROSTER",
                "fallbackUsed": len(ranked) < min(5, len(role_pool)),
                "priority": (["SAME_TEAM_HANDCUFF", "ROTATION_PAIR", "QUALITY_REPLACEMENT"] if role == "P" else ["COMPLEMENT_ROSTER", "STACK_TEAM", "CALENDAR_ADVANTAGE", "QUALITY_REPLACEMENT"]),
            },
        }
        self._alternative_cache[key] = dict(result)
        return result

    def _expected_for_portfolio(
        self,
        player: Dict[str, Any],
        existing_roster: Sequence[Dict[str, Any]],
        composition: Dict[str, int],
        rotation: Optional[Dict[str, Any]] = None,
        return_breakdown: bool = False,
    ) -> Any:
        absolute = self._absolute_value(player)
        temp = dict(player)
        temp["absolute_value"] = absolute
        # Ridondanza: peso derivato dalla copertura attuale del ruolo e dalla similarita' di profilo.
        fake_team = {"roster": list(existing_roster)}
        redundancy = self._redundancy_profile(temp, fake_team, composition)
        complementarity = 0.0
        if rotation:
            complementarity = absolute * _float(rotation.get("score"), 0.0)
        adjusted = max(0.0, absolute - redundancy["penalty"] + complementarity)
        if return_breakdown:
            return {
                "absolute": absolute,
                "marginal": adjusted,
                "redundancyPenalty": redundancy["penalty"],
                "redundancySimilarity": redundancy["similarity"],
                "redundancyCoverage": redundancy["coverage"],
                "complementarityBonus": complementarity,
            }
        return adjusted

    def _portfolio_metrics(
        self,
        roster: Sequence[Dict[str, Any]],
        existing_roster: Optional[Sequence[Dict[str, Any]]] = None,
        composition: Optional[Dict[str, int]] = None,
        budget: float = 0.0,
        matchdays: int = 0,
        covariance_matrix: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        composition = composition or {r: 0 for r in ROLES}
        existing_raw = list(existing_roster or [])
        existing = (
            self._enrich_existing_roster(existing_raw, budget, matchdays)
            if existing_raw and not all("ruolo" in p and "fm" in p for p in existing_raw)
            else [dict(p) for p in existing_raw]
        )
        new_players = [dict(p) for p in roster]
        if not existing and not new_players:
            return {
                "expected": 0.0,
                "risk": 0.0,
                "utility": 0.0,
                "teamConcentration": 0.0,
                "commonFactorExposure": 0.0,
                "statusRisk": 0.0,
                "marginalExpected": 0.0,
                "redundancyPenalty": 0.0,
                "complementarityBonus": 0.0,
            }

        # Gli acquisti nuovi sono ordinati dal valore assoluto piu' alto al piu' basso:
        # la ridondanza colpisce il profilo aggiuntivo, non svaluta retroattivamente
        # giocatori gia' acquistati (costo sommerso).
        ordered_new = sorted(new_players, key=self._absolute_value, reverse=True)
        adjusted_new: List[Tuple[Dict[str, Any], Dict[str, float]]] = []
        comparison_roster = list(existing)
        for player in ordered_new:
            rotation = player.get("rotation") if player.get("ruolo") == "P" else None
            details = self._expected_for_portfolio(player, comparison_roster, composition, rotation, True)
            adjusted_new.append((player, details))
            comparison_roster.append(player)

        existing_values = [self._absolute_value(player) for player in existing]
        adjusted_values = existing_values + [details["marginal"] for _, details in adjusted_new]
        full_roster = existing + ordered_new
        expected_total = sum(adjusted_values)

        redundancy_penalty = sum(details["redundancyPenalty"] for _, details in adjusted_new)
        complementarity_bonus = sum(details["complementarityBonus"] for _, details in adjusted_new)
        status_risks = [
            self._absolute_value(player) * _float(player.get("status_risk"), 0.0)
            for player in full_roster
        ]

        by_team: Dict[str, float] = {}
        for player, value in zip(full_roster, adjusted_values):
            club = str(player.get("squadra") or "N/D")
            by_team[club] = by_team.get(club, 0.0) + value
        shares = [v / expected_total for v in by_team.values()] if expected_total else []
        hhi = sum(x * x for x in shares)
        teams_used = max(1, len(shares))
        diversified_hhi = 1.0 / teams_used
        normalized_concentration = 0.0
        if teams_used > 1:
            normalized_concentration = max(
                0.0,
                (hhi - diversified_hhi) / max(1e-9, 1.0 - diversified_hhi),
            )

        status_variance = sum(x * x for x in status_risks)
        matrix_variance = 0.0
        covariance_available = isinstance(covariance_matrix, dict) and bool(covariance_matrix)
        if covariance_available:
            ids = [str(_int(p.get("id"), 0)) for p in full_roster]
            for i, player_id in enumerate(ids):
                row = covariance_matrix.get(player_id)
                if row is None and player_id.isdigit():
                    row = covariance_matrix.get(int(player_id))
                row = row if isinstance(row, dict) else {}
                own = row.get(player_id, row.get(int(player_id), 0.0)) if player_id.isdigit() else row.get(player_id, 0.0)
                matrix_variance += max(0.0, _float(own))
                for other_id in ids[i + 1:]:
                    covariance = row.get(other_id, row.get(int(other_id), 0.0)) if other_id.isdigit() else row.get(other_id, 0.0)
                    matrix_variance += 2.0 * _float(covariance)
        else:
            team_covariance = 0.0
            for club, value in by_team.items():
                club_risks = [
                    _float(p.get("status_risk"), 0.0)
                    for p in full_roster
                    if str(p.get("squadra") or "N/D") == club
                ]
                club_risk = median(club_risks) if club_risks else 0.0
                team_covariance += (value * club_risk) ** 2
            matrix_variance = team_covariance * (1.0 + normalized_concentration)

        total_risk = math.sqrt(max(0.0, status_variance + matrix_variance))
        utility = expected_total - total_risk
        marginal_expected = sum(details["marginal"] for _, details in adjusted_new)
        return {
            "expected": expected_total,
            "risk": total_risk,
            "utility": utility,
            "teamConcentration": hhi,
            "commonFactorExposure": normalized_concentration,
            "statusRisk": sum(status_risks) / max(1.0, expected_total),
            "marginalExpected": marginal_expected,
            "redundancyPenalty": redundancy_penalty,
            "complementarityBonus": complementarity_bonus,
        }

    @staticmethod
    def _combination_count(needs: Dict[str, int], pools: Dict[str, List[Dict[str, Any]]]) -> int:
        total = 1
        for role, count in needs.items():
            n = len(pools.get(role, []))
            if count <= 0:
                continue
            if n < count:
                return 0
            total *= math.comb(n, count)
            if total > 10**18:
                return total
        return total

    def _adaptive_limits(
        self,
        pools: Dict[str, List[Dict[str, Any]]],
        needs: Dict[str, int],
        config: AdvisorConfig,
    ) -> Tuple[int, int, bool]:
        total_open = max(1, sum(needs.values()))
        candidate_sizes = []
        for role, pool in pools.items():
            if not pool:
                continue
            candidate_sizes.append(min(len(pool), max(1, math.ceil(math.sqrt(len(pool))))))
        derived_candidates = max(candidate_sizes, default=1)
        role_candidates = config.max_role_candidates or derived_candidates
        role_candidates = max(1, role_candidates)
        reduced_pools = {role: pool[: min(len(pool), role_candidates)] for role, pool in pools.items()}
        combination_count = self._combination_count(needs, reduced_pools)
        max_pool = max((len(v) for v in reduced_pools.values()), default=1)
        derived_beam = max(1, min(max_pool, math.ceil(math.sqrt(max(1, sum(len(v) for v in reduced_pools.values()))))))
        beam_width = config.beam_width or derived_beam
        exact_limit = config.exact_search_limit or max(beam_width, beam_width * total_open)
        use_exact = bool(combination_count and combination_count <= exact_limit)
        return role_candidates, max(1, beam_width), use_exact

    def _fast_partial_score(
        self,
        roster: Sequence[Dict[str, Any]],
        existing_roster: Optional[Sequence[Dict[str, Any]]],
        composition: Dict[str, int],
    ) -> float:
        """Score leggero per il beam: evita di ricalcolare l'intero portafoglio ad ogni espansione."""
        existing = existing_roster or []
        total = 0.0
        variance = 0.0
        for player in roster:
            details = self._expected_for_portfolio(player, existing, composition, player.get("rotation"), True)
            total += details["marginal"]
            risk_component = details["absolute"] * _float(player.get("status_risk"), 0.0)
            variance += risk_component * risk_component
        return total - math.sqrt(max(0.0, variance))

    def _optimize_roster(
        self,
        available: List[Dict[str, Any]],
        needs: Dict[str, int],
        budget: float,
        forced: Optional[Sequence[Tuple[Dict[str, Any], float]]] = None,
        existing_roster: Optional[Sequence[Dict[str, Any]]] = None,
        composition: Optional[Dict[str, int]] = None,
        config: Optional[AdvisorConfig] = None,
        covariance_matrix: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = config or AdvisorConfig()
        composition = composition or {r: 0 for r in ROLES}
        forced = list(forced or [])
        roster = [dict(p) for p, _ in forced]
        spent = sum(max(0.0, float(price)) for _, price in forced)
        needs_left = dict(needs)
        for player, _ in forced:
            role = player["ruolo"]
            needs_left[role] = max(0, needs_left.get(role, 0) - 1)

        if spent > budget + 1e-9:
            return {"roster": [], "spent": float("inf"), "solver": "infeasible", **self._portfolio_metrics([], existing_roster, composition)}

        selected_ids = {int(p["id"]) for p in roster}
        pools: Dict[str, List[Dict[str, Any]]] = {}
        for role in ROLES:
            count = needs_left.get(role, 0)
            if count <= 0:
                pools[role] = []
                continue
            pool = [p for p in available if p["ruolo"] == role and int(p["id"]) not in selected_ids]
            pool.sort(
                key=lambda p: (
                    self._absolute_value(p) / max(1e-9, _float(p.get("price_credits"), 1.0)),
                    self._absolute_value(p),
                    _float(p.get("overall")),
                ),
                reverse=True,
            )
            pools[role] = pool

        role_candidates, beam_width, use_exact = self._adaptive_limits(pools, needs_left, config)
        pools = {role: pool[:role_candidates] for role, pool in pools.items()}

        def score_state(r: Sequence[Dict[str, Any]], c: float) -> float:
            return self._fast_partial_score(r, existing_roster, composition)

        states: List[Tuple[List[Dict[str, Any]], float]] = [(list(roster), spent)]
        if use_exact:
            # Enumerazione controllata per casi piccoli: preserva l'ottimo senza costi proibitivi.
            for role in ROLES:
                count = needs_left.get(role, 0)
                if count <= 0:
                    continue
                candidates = pools.get(role, [])
                next_states: List[Tuple[List[Dict[str, Any]], float]] = []
                for current_roster, current_spent in states:
                    used = {int(p["id"]) for p in current_roster}
                    for combo in __import__("itertools").combinations(candidates, count):
                        ids = {int(p["id"]) for p in combo}
                        if ids & used:
                            continue
                        cost = sum(max(1e-9, _float(p.get("price_credits"), 0.0)) for p in combo)
                        total_spent = current_spent + cost
                        if total_spent <= budget + 1e-9:
                            next_states.append((current_roster + list(combo), total_spent))
                states = next_states
                if not states:
                    return {"roster": [], "spent": float("inf"), "solver": "exact", **self._portfolio_metrics([], existing_roster, composition)}
            best = max(states, key=lambda item: self._portfolio_metrics(item[0], existing_roster, composition)["utility"])
            metrics = self._portfolio_metrics(best[0], existing_roster, composition, covariance_matrix=covariance_matrix)
            return {"roster": best[0], "spent": best[1], "solver": "exact", "combinationCount": self._combination_count(needs_left, pools), **metrics}

        # Beam search adattivo con elitism: conserva sempre il migliore stato per ruolo.
        for role in ROLES:
            count = needs_left.get(role, 0)
            if count <= 0:
                continue
            candidates = pools.get(role, [])
            for _ in range(count):
                next_states: List[Tuple[List[Dict[str, Any]], float]] = []
                for current_roster, current_spent in states:
                    used = {int(p["id"]) for p in current_roster}
                    for candidate in candidates:
                        pid = int(candidate["id"])
                        if pid in used:
                            continue
                        cost = max(0.0, _float(candidate.get("price_credits"), 0.0))
                        new_spent = current_spent + cost
                        if new_spent <= budget + 1e-9:
                            next_states.append((current_roster + [candidate], new_spent))
                if not next_states:
                    return {"roster": [], "spent": float("inf"), "solver": "beam", **self._portfolio_metrics([], existing_roster, composition)}
                scored = [(score_state(r, c), r, c) for r, c in next_states]
                scored.sort(key=lambda x: x[0], reverse=True)
                states = [(r, c) for _, r, c in scored[:beam_width]]

        best = max(states, key=lambda item: self._portfolio_metrics(item[0], existing_roster, composition)["utility"])
        metrics = self._portfolio_metrics(best[0], existing_roster, composition, covariance_matrix=covariance_matrix)
        return {
            "roster": best[0],
            "spent": best[1],
            "solver": "beam",
            "beamWidth": beam_width,
            "roleCandidates": role_candidates,
            **metrics,
        }

    def _counterfactual_frontier(
        self,
        available: List[Dict[str, Any]],
        needs: Dict[str, int],
        team: Dict[str, Any],
        player: Dict[str, Any],
        legal_max: int,
        minimum: int,
        increment: int,
        current_bid: int,
        market_info: Dict[str, Any],
        composition: Dict[str, int],
        strategic_budget: float,
        existing_roster: Sequence[Dict[str, Any]],
        config: AdvisorConfig,
        covariance_matrix: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        remaining = [p for p in available if int(p["id"]) != int(player["id"])]
        context_signature = _stable_hash({
            "player": player["id"],
            "team": team.get("id"),
            "teamRoster": self._roster_signature(team),
            "needs": needs,
            "strategicBudget": strategic_budget,
            "legalMax": legal_max,
            "minimum": minimum,
            "increment": increment,
            "market": market_info,
            "data": self._data_revision,
            "covariance": covariance_matrix,
        })

        baseline_key = f"baseline:{context_signature}"
        baseline = self._frontier_cache.get(baseline_key)
        if baseline is None:
            baseline = self._optimize_roster(
                remaining,
                needs,
                strategic_budget,
                existing_roster=existing_roster,
                composition=composition,
                config=config,
                covariance_matrix=covariance_matrix,
            )
            self._frontier_cache[baseline_key] = dict(baseline)
        baseline_utility = _float(baseline.get("utility"), float("-inf"))
        if not math.isfinite(baseline_utility):
            baseline_utility = 0.0

        model_price = max(float(minimum), _float(player.get("price_credits"), minimum))
        static_frontier = self._frontier_cache.get(f"frontier:{context_signature}")
        role_market = _float(market_info.get("roleMedian"), model_price)
        role_high = _float(market_info.get("roleHigh"), role_market)
        upper_hint = min(legal_max, max(minimum, int(math.ceil(max(role_high, model_price, float(current_bid or minimum))))))
        start = max(minimum, int(current_bid or minimum))
        start = min(start, legal_max) if legal_max > 0 else start
        if start > upper_hint:
            start = upper_hint

        evaluated: Dict[int, Dict[str, Any]] = {}

        def evaluate(price: int) -> Dict[str, Any]:
            price = int(max(minimum, min(legal_max, price)))
            cache_key = f"plan:{context_signature}:{price}"
            if price not in evaluated:
                cached_plan = self._forced_plan_cache.get(cache_key)
                if cached_plan is not None:
                    evaluated[price] = cached_plan
                else:
                    forced_player = dict(player)
                    plan = self._optimize_roster(
                        remaining,
                        needs,
                        strategic_budget,
                        forced=[(forced_player, price)],
                        existing_roster=existing_roster,
                        composition=composition,
                        config=config,
                        covariance_matrix=covariance_matrix,
                    )
                    evaluated[price] = plan
                    self._forced_plan_cache[cache_key] = dict(plan)
            return evaluated[price]

        def delta(price: int) -> Tuple[float, Dict[str, Any]]:
            plan = evaluate(price)
            return _float(plan.get("utility"), float("-inf")) - baseline_utility, plan

        if static_frontier is not None and legal_max >= minimum:
            current_price = max(minimum, min(legal_max, int(current_bid or minimum)))
            current_plan = evaluate(current_price)
            return {
                **static_frontier,
                "baseline": baseline,
                "baselineUtility": baseline_utility,
                "baselineExpected": _float(baseline.get("expected")),
                "currentPlan": current_plan,
                "currentUtilityDelta": _float(current_plan.get("utility"), 0.0) - baseline_utility,
                "evaluatedPrices": 1,
            }

        if legal_max < minimum:
            return {
                "baseline": baseline,
                "candidatePlan": None,
                "baselineUtility": baseline_utility,
                "baselineExpected": _float(baseline.get("expected")),
                "maxBid": 0,
                "utilityDelta": 0.0,
                "currentPlan": baseline,
                "currentUtilityDelta": 0.0,
                "firstBadPrice": minimum,
                "evaluatedPrices": 0,
                "frontierStable": True,
            }

        low_delta, low_plan = delta(minimum)
        if low_delta <= 0:
            current_price = max(minimum, min(legal_max, int(current_bid or minimum)))
            current_plan = evaluate(current_price)
            return {
                "baseline": baseline,
                "candidatePlan": None,
                "baselineUtility": baseline_utility,
                "baselineExpected": _float(baseline.get("expected")),
                "maxBid": 0,
                "utilityDelta": low_delta,
                "currentPlan": current_plan,
                "currentUtilityDelta": _float(current_plan.get("utility"), 0.0) - baseline_utility,
                "firstBadPrice": minimum,
                "evaluatedPrices": len(evaluated),
                "frontierStable": True,
            }

        high_delta, high_plan = delta(upper_hint)
        max_good = upper_hint
        best_plan = high_plan
        if high_delta <= 0:
            max_good = minimum
            best_plan = low_plan
            step = max(1, int(round(increment)))
            low_index = 0
            high_index = max(0, (upper_hint - minimum) // step)
            while low_index <= high_index:
                mid_index = (low_index + high_index) // 2
                price = minimum + mid_index * step
                current_delta_value, current_plan = delta(price)
                if current_delta_value > 0:
                    max_good = price
                    best_plan = current_plan
                    low_index = mid_index + 1
                else:
                    high_index = mid_index - 1

        # Verifica locale attorno alla soglia per correggere eventuali oscillazioni euristiche.
        local_steps = config.local_verification_steps or 1
        step = max(1, int(round(increment)))
        candidate_prices = set()
        for offset in range(-local_steps, local_steps + 1):
            candidate_prices.add(max(minimum, min(upper_hint, max_good + offset * step)))
        local_results = []
        for price in sorted(candidate_prices):
            d, plan = delta(price)
            local_results.append((price, d, plan))
        good_prices = [item for item in local_results if item[1] > 0]
        if good_prices:
            max_good = max(item[0] for item in good_prices)
            best_plan = next(item[2] for item in good_prices if item[0] == max_good)

        first_bad = max_good + step
        if first_bad > legal_max:
            first_bad = None

        current_price = max(minimum, min(legal_max, int(current_bid or minimum)))
        current_plan = evaluate(current_price)
        current_delta = _float(current_plan.get("utility"), 0.0) - baseline_utility

        observed_deltas = [item[1] for item in sorted(local_results)]
        monotone = all(a >= b - 1e-8 for a, b in zip(observed_deltas, observed_deltas[1:]))
        static_result = {
            "candidatePlan": best_plan,
            "maxBid": _round_bid(max_good, minimum, increment),
            "utilityDelta": _float(best_plan.get("utility"), 0.0) - baseline_utility,
            "firstBadPrice": first_bad,
            "frontierStable": monotone,
        }
        self._frontier_cache[f"frontier:{context_signature}"] = dict(static_result)
        return {
            **static_result,
            "baseline": baseline,
            "baselineUtility": baseline_utility,
            "baselineExpected": _float(baseline.get("expected")),
            "currentPlan": current_plan,
            "currentUtilityDelta": current_delta,
            "evaluatedPrices": len(evaluated),
        }

    def _effective_opponent_demand(
        self,
        team: Dict[str, Any],
        teams: List[Dict[str, Any]],
        role: str,
        composition: Dict[str, int],
    ) -> Dict[str, Any]:
        opponents = [t for t in teams if t.get("id") != team.get("id")]
        if not opponents:
            return {"effectiveDemand": 0.0, "count": 0, "medianCredits": 0.0, "details": []}
        credits = [max(0.0, _float(t.get("credits"))) for t in opponents]
        median_credits = median(credits) if credits else 0.0
        details = []
        effective = 0.0
        for opponent in opponents:
            need = self._role_need(opponent, role, composition)
            open_slots = sum(self._role_need(opponent, r, composition) for r in ROLES)
            available_ratio = (_float(opponent.get("credits")) / max(1.0, median_credits)) if median_credits > 0 else 0.0
            slot_pressure = need / max(1, open_slots)
            contribution = need * available_ratio * max(slot_pressure, 1.0 / max(1, open_slots))
            effective += contribution
            details.append({
                "id": opponent.get("id"),
                "name": opponent.get("name"),
                "credits": _float(opponent.get("credits")),
                "need": need,
                "openSlots": open_slots,
                "spendingPower": available_ratio,
                "effectiveDemand": contribution,
            })
        return {
            "effectiveDemand": effective,
            "count": sum(1 for d in details if d["need"] > 0),
            "medianCredits": median_credits,
            "details": details,
        }

    def _role_market_context(self, market: Dict[str, Any], role: str, player_price: float) -> Dict[str, float]:
        band = market.get("role_band", {}).get(role, {})
        median_ratio = _float(band.get("median"), 1.0)
        low_ratio = _float(band.get("low"), median_ratio)
        high_ratio = _float(band.get("high"), median_ratio)
        return {
            "roleMedian": max(player_price, player_price * median_ratio),
            "roleLow": max(player_price, player_price * low_ratio),
            "roleHigh": max(player_price, player_price * high_ratio),
        }

    def _build_context(self, state: Dict[str, Any], team: Dict[str, Any], config: AdvisorConfig) -> Dict[str, Any]:
        key = self._state_context_key(state, team)
        cached = self._context_cache.get(key)
        if cached is not None:
            return cached

        rules = state.get("rules") or {}
        budget = _float(rules.get("starting_credits"), 0.0)
        composition = {role: int((rules.get("composition") or {}).get(role, 0)) for role in ROLES}
        matchdays = _int(rules.get("matchdays"), 38)
        remaining = self._all_role_players(budget, state, matchdays)
        self._tierize(remaining)
        records = self._assigned_records(state, budget, matchdays)
        market = self._market_model(records, config)
        scarcity = self._scarcity(remaining, list(state.get("teams") or []), composition)
        global_targets = self._role_targets(remaining, list(state.get("teams") or []), composition, budget)
        context = {
            "key": key,
            "covariance": state.get("advisor_covariance") or rules.get("advisor_covariance"),
            "budget": budget,
            "composition": composition,
            "matchdays": matchdays,
            "remaining": remaining,
            "records": records,
            "market": market,
            "scarcity": scarcity,
            "globalTargets": global_targets,
        }
        self._context_cache[key] = context
        return context

    def _assigned_records(self, state: Dict[str, Any], budget: float, matchdays: int) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for player_id, assignment in (state.get("assigned") or {}).items():
            player = self._player(int(player_id), budget, matchdays)
            if not player:
                continue
            price = _float((assignment or {}).get("price"))
            if price > 0:
                records.append({"player": player, "price": price, "owner": (assignment or {}).get("owner")})
        self._tierize([x["player"] for x in records])
        return records

    def advise(self, state: Dict[str, Any], player_id: int, team_id: Optional[str] = None, current_price: Optional[float] = None) -> Dict[str, Any]:
        config = AdvisorConfig.from_state(state)
        rules = state.get("rules") or {}
        teams = list(state.get("teams") or [])
        if not teams:
            return {"recommendation": "INELIGIBLE", "reasons": ["Configura prima le squadre dell'asta."], "risks": []}

        # my_team_id ha priorita' sul bidder: l'Advisor ragiona sempre sulla squadra strategica.
        strategic_team_id = state.get("my_team_id") or state.get("advisor_team_id") or team_id
        team = next((t for t in teams if t.get("id") == strategic_team_id), teams[0])
        owner_index = next((i for i, t in enumerate(teams) if t.get("id") == team.get("id")), 0)

        minimum = max(1.0, _float(rules.get("minimum_price"), 1.0))
        increment = max(0.01, _float(rules.get("bid_increment"), 1.0))
        reserve = max(0.0, _float(rules.get("reserve_per_slot"), 0.0))
        context = self._build_context(state, team, config)
        player = self._player(int(player_id), context["budget"], context["matchdays"])
        if not player:
            return {"recommendation": "INELIGIBLE", "reasons": ["Giocatore non trovato nel database."], "risks": []}

        remaining = context["remaining"]
        candidate = next((p for p in remaining if int(p["id"]) == int(player["id"])), player)
        player = candidate
        role = player["ruolo"]
        needs = self._needs(team, context["composition"])
        open_slots = sum(needs.values())

        if role not in ROLES or needs.get(role, 0) <= 0:
            return {
                "kind": "candidate",
                "recommendation": "INELIGIBLE",
                "purpose": "NO_FIT",
                "idealMin": 0,
                "idealMax": 0,
                "maxBid": 0,
                "legalMax": 0,
                "confidence": 1.0,
                "reasons": [f"Nessun posto disponibile per il ruolo {role}."],
                "risks": [],
                "alternatives": [],
                "summary": {
                    "owner": owner_index,
                    "ownerName": team.get("name"),
                    "credits": _float(team.get("credits")),
                    "slotsOpen": open_slots,
                },
            }

        credits = max(0.0, _float(team.get("credits")))
        future_slots = max(0, open_slots - 1)
        legal_raw = credits - future_slots * reserve
        legal_max = max(0, _round_bid(legal_raw, minimum, increment)) if legal_raw >= minimum else 0

        strategic = self._strategic_budget(
            team,
            needs,
            context["composition"],
            context["globalTargets"],
            teams,
            minimum,
            remaining,
        )
        strategic_budget = min(credits, max(0.0, strategic["budget"]))
        strategic_legal_max = max(0, _round_bid(min(legal_max, strategic_budget), minimum, increment)) if strategic_budget >= minimum else 0

        market = context["market"]
        scarcity = context["scarcity"]
        role_market = _float(market["role_inflation"].get(role), 1.0)
        role_market_ctx = self._role_market_context(market, role, _float(player["price_credits"], minimum))
        effective_demand = self._effective_opponent_demand(team, teams, role, context["composition"])
        supply = max(1, scarcity[role]["supply"])
        demand_pressure = effective_demand["effectiveDemand"] / supply
        market_cost = max(minimum, role_market_ctx["roleMedian"] * max(1.0, 1.0 + demand_pressure))

        status_reference = self._status_reference(remaining)
        status_profile = self._status_profile(player, status_reference)
        player["status_category"] = status_profile["category"]
        player["availability"] = status_profile["availability"]
        player["status_risk"] = status_profile["risk"]
        absolute_value = self._absolute_value(player)
        player["absolute_value"] = absolute_value

        existing_roster = self._enrich_existing_roster(team.get("roster") or [], context["budget"], context["matchdays"])
        team_for_logic = dict(team)
        team_for_logic["roster"] = existing_roster
        rotation = self._rotation_analysis(player, team_for_logic, state.get("current_matchday")) if role == "P" else {"available": False, "rotationDelta": 0.0, "sameTeamHandcuff": False, "score": None}
        player["rotation"] = rotation
        marginal_details = self._expected_for_portfolio(player, existing_roster, context["composition"], rotation, True)

        alternative_data = self._personalized_alternatives(
            state, team, player, remaining, existing_roster, context["composition"],
            role_market, minimum, increment, state.get("current_matchday")
        )
        alternatives = alternative_data["alternatives"]
        valid_alternatives_count = int(alternative_data.get("validAlternativesCount", len(alternatives)))
        role_pool = [p for p in remaining if p["ruolo"] == role and int(p["id"]) != int(player["id"])]

        global_tiers = {
            tier: sum(1 for p in [x for x in remaining if x["ruolo"] == role] if p.get("tier") == tier)
            for tier in TIER_LABELS
        }
        timing = {
            "playersToCall": len(role_pool) + 1,
            "eliteRemaining": global_tiers.get("ELITE", 0),
            "premiumRemaining": global_tiers.get("PREMIUM", 0),
            "playersNeeded": needs.get(role, 0),
            "futureSupplyRatio": len(role_pool) / max(1, needs.get(role, 0)),
        }

        frontier = self._counterfactual_frontier(
            remaining,
            needs,
            team,
            player,
            strategic_legal_max,
            int(math.ceil(minimum)),
            increment,
            max(
                int(math.ceil(minimum)),
                _int(
                    current_price
                    if current_price is not None
                    else ((state.get("current_auction") or {}).get("current_price")),
                    int(math.ceil(minimum)),
                ),
            ),
            {**role_market_ctx, "roleMedian": market_cost},
            context["composition"],
            strategic_budget,
            team.get("roster") or [],
            config,
        )

        max_bid = min(legal_max, strategic_legal_max, frontier["maxBid"])
        current_bid = _int(
            current_price
            if current_price is not None
            else ((state.get("current_auction") or {}).get("current_price")),
            int(math.ceil(minimum)),
        )
        next_bid = max(int(math.ceil(minimum)), current_bid + max(1, int(round(increment)))) if current_bid >= minimum else int(math.ceil(minimum))
        next_bid = _round_bid(next_bid, minimum, increment)

        market_low = max(minimum, role_market_ctx["roleLow"] * max(1.0, 1.0 + demand_pressure))
        market_high = max(market_low, role_market_ctx["roleHigh"] * max(1.0, 1.0 + demand_pressure))
        if max_bid:
            ideal_min = _round_bid(min(max_bid, market_low), minimum, increment)
            ideal_max = _round_bid(min(max_bid, market_high), minimum, increment)
            ideal_min = min(ideal_min, ideal_max)
        else:
            ideal_min = ideal_max = 0

        current_delta = _float(frontier["currentUtilityDelta"], 0.0)
        best_delta = _float(frontier["utilityDelta"], 0.0)
        keeper_complementarity = (
            role == "P"
            and bool(rotation.get("available"))
            and (
                bool(rotation.get("sameTeamHandcuff"))
                or _float(rotation.get("rotationDelta"), 0.0) > 0.0
            )
        )
        if max_bid < next_bid:
            recommendation = "PASS"
        elif current_delta <= 0 and not keeper_complementarity:
            recommendation = "PASS"
        elif max_bid >= market_cost and current_bid <= market_cost:
            recommendation = "STRONG_BUY"
        elif max_bid >= market_cost:
            recommendation = "BID"
        else:
            recommendation = "VALUE_ONLY"

        purpose = self._purpose(player, team, needs, rotation)
        marginal_presentation = self._marginal_gain_presentation(
            player, role_pool, frontier["baselineUtility"], frontier["currentUtilityDelta"]
        )
        tier = str(player.get("tier") or "STANDARD")
        role_rank = _int(player.get("role_rank"), 0)

        # Confidence costruita da evidenze osservabili, senza soglie arbitrarie.
        market_conf = _float(market.get("confidence"), 0.0)
        status_conf = status_profile["sourceQuality"]
        alternative_conf = min(1.0, len(alternatives) / max(1, len(TIER_LABELS) - 1))
        frontier_conf = 1.0 if frontier.get("frontierStable") else 0.5
        solver_conf = 1.0 if frontier.get("baseline", {}).get("solver") == "exact" else 0.75
        rotation_conf = 1.0 if rotation.get("available") else (0.5 if role == "P" else 1.0)
        confidence = sum((market_conf, status_conf, alternative_conf, frontier_conf, solver_conf, rotation_conf)) / 6.0
        confidence = max(0.0, min(1.0, confidence))

        reasons = [
            f"Valore assoluto: {absolute_value:.2f}; valore marginale stimato: {marginal_details['marginal']:.2f}.",
            f"Vantaggio attuale: {marginal_presentation['percentage']:+.1f}% — {marginal_presentation['label']}.",
            f"Categoria {tier}, posizione #{role_rank} nel ruolo.",
            f"Prezzo modello app: {player['price_percentage']:.1f}% = circa {player['price_credits']:.0f} crediti.",
            f"Mercato ruolo: circa {market_cost:.0f} crediti; domanda effettiva {effective_demand['effectiveDemand']:.2f}.",
            f"Scarsità qualitativa: {scarcity[role]['qualitativeSupply']} profili utili su {scarcity[role]['supply']} disponibili.",
            f"Budget strategico: {strategic_budget:.0f}; riserva futura stimata: {strategic['futureReserve']:.0f}.",
            f"Rosa senza candidato: utilità {frontier['baselineUtility']:.2f}; vantaggio al prezzo corrente: {current_delta:+.2f}.",
        ]
        reasons.extend(status_profile["reasons"])
        if rotation.get("sameTeamHandcuff") or rotation.get("rotationDelta", 0.0) > 0:
            reasons.append(
                f"Complementarità portieri: miglioramento rotazione {rotation.get('rotationDelta', 0.0):.2f}; score {rotation.get('score')}."
            )
        if role == "P" and existing_roster and keeper_complementarity:
            if rotation.get("sameTeamHandcuff"):
                reasons.append("Hai gia' un portiere: questo profilo viene valutato come handcuff della stessa squadra, non come semplice doppione di un TOP.")
            else:
                reasons.append("Hai gia' un portiere: il modello privilegia la complementarita' di calendario/rotazione rispetto al valore assoluto del secondo TOP.")

        risks: List[str] = []
        if market.get("records", 0) <= 0:
            risks.append("Nessun prezzo storico osservato: il mercato è stimato principalmente dal modello.")
        elif market_conf < 0.5:
            risks.append("Confidenza del mercato ancora bassa per numero limitato di acquisti.")
        if scarcity[role]["qualitativeSupply"] < needs.get(role, 0):
            risks.append("Le alternative qualitativamente affidabili non coprono tutti gli slot residui del ruolo.")
        if status_profile["risk"] > 0:
            risks.append("Lo status/disponibilità riduce il valore atteso.")
        if max_bid and market_cost > max_bid:
            risks.append(f"Il mercato stimato ({market_cost:.0f}) supera il MAX BID strategico ({max_bid}).")
        if frontier.get("frontierStable") is False:
            risks.append("La frontiera controfattuale mostra instabilità locale dell'euristica.")
        if purpose == "COVERAGE" and marginal_details["marginal"] < absolute_value:
            risks.append("Il giocatore replica parzialmente un profilo già coperto nel ruolo.")

        summary = {
            "owner": owner_index,
            "ownerName": team.get("name"),
            "myTeamId": team.get("id"),
            "credits": int(credits),
            "strategicBudget": round(strategic_budget, 2),
            "futureBudgetReserve": round(strategic["futureReserve"], 2),
            "rosterSize": len(team.get("roster") or []),
            "slotsOpen": open_slots,
            "candidateValue": round(absolute_value, 3),
            "absoluteValue": round(absolute_value, 3),
            "marginalValue": round(marginal_details["marginal"], 3),
            "marginalGainPercentage": marginal_presentation["percentage"],
            "marginalGainLevel": marginal_presentation["level"],
            "marginalGainLabel": marginal_presentation["label"],
            "redundancyPenalty": round(marginal_details["redundancyPenalty"], 3),
            "complementarityBonus": round(marginal_details["complementarityBonus"], 3),
            "tier": tier,
            "roleRank": role_rank,
            "rolePercentile": player.get("role_percentile"),
            "status": status_profile["raw"],
            "statusCategory": status_profile["category"],
            "availability": round(status_profile["availability"], 3),
            "statusRisk": round(status_profile["risk"], 3),
            "estimatedMarketPrice": int(_round_bid(market_cost, minimum, increment)),
            "marketInflation": round(market["inflation"], 3),
            "roleInflation": round(role_market, 3),
            "marketConfidence": round(market_conf, 3),
            "roleScarcity": round(scarcity[role]["ratio"], 3),
            "roleSupply": int(scarcity[role]["supply"]),
            "roleDemand": int(scarcity[role]["demand"]),
            "qualitativeSupply": int(scarcity[role]["qualitativeSupply"]),
            "opponentDemand": effective_demand["count"],
            "effectiveOpponentDemand": round(effective_demand["effectiveDemand"], 3),
            "opponentSpendingMedian": round(effective_demand["medianCredits"], 2),
            "sourcePricePercentage": round(_float(player["price_percentage"]), 1),
            "sourcePriceCredits": round(_float(player["price_credits"])),
            "overall": player["overall"],
            "fm": round(player["fm"], 2),
            "mv": round(player["mv"], 2),
            "titolarita": round(player["titolarita"], 1),
            "replacement": alternatives[0]["name"] if alternatives else None,
            "alternativesCount": int(valid_alternatives_count),
            "validAlternativesCount": int(valid_alternatives_count),
            "roleAlternativeCount": int(valid_alternatives_count),
            "alternativeStrategy": alternative_data.get("strategy", {}),
            "playersToCall": timing["playersToCall"],
            "eliteRemaining": timing["eliteRemaining"],
            "premiumRemaining": timing["premiumRemaining"],
            "futureSupplyRatio": round(timing["futureSupplyRatio"], 3),
            "baselineExpectedValue": round(frontier["baselineExpected"], 3),
            "baselineUtility": round(frontier["baselineUtility"], 3),
            "utilityDeltaAtCurrentBid": round(current_delta, 3),
            "currentBid": int(current_bid),
            "nextBid": int(next_bid),
            "candidateExpectedValueAtMax": round(_float((frontier.get("candidatePlan") or {}).get("expected")), 3),
            "candidateRiskAtMax": round(_float((frontier.get("candidatePlan") or {}).get("risk")), 3),
            "candidateUtilityAtMax": round(_float((frontier.get("candidatePlan") or {}).get("utility")), 3),
            "utilityDeltaAtMax": round(best_delta, 3),
            "firstBadPrice": frontier.get("firstBadPrice"),
            "frontierStable": frontier.get("frontierStable"),
            "solver": (frontier.get("baseline") or {}).get("solver"),
            "teamConcentration": round(_float((frontier.get("candidatePlan") or {}).get("teamConcentration")), 4),
            "rotationAvailable": bool(rotation.get("available")),
            "rotationDelta": round(_float(rotation.get("rotationDelta")), 4),
            "rotationScore": rotation.get("score"),
            "bidderIndependent": True,
        }

        return {
            "kind": "candidate",
            "recommendation": recommendation,
            "purpose": purpose,
            "idealMin": int(ideal_min),
            "idealMax": int(ideal_max),
            "maxBid": int(max_bid),
            "legalMax": int(legal_max),
            "marginalGainPercentage": marginal_presentation["percentage"],
            "marginalGainLevel": marginal_presentation["level"],
            "marginalGainLabel": marginal_presentation["label"],
            "strategicMaxBid": int(strategic_legal_max),
            "confidence": round(confidence, 3),
            "reasons": reasons,
            "risks": risks,
            "alternatives": alternatives,
            "validAlternativesCount": int(valid_alternatives_count),
            "alternativeStrategy": alternative_data.get("strategy", {}),
            "summary": summary,
        }

    def overview(self, state: Dict[str, Any], team_id: Optional[str] = None) -> Dict[str, Any]:
        config = AdvisorConfig.from_state(state)
        teams = list(state.get("teams") or [])
        if not teams:
            return {"kind": "overview", "rolePlan": {}, "credits": 0, "slotsOpen": 0}
        strategic_team_id = state.get("my_team_id") or state.get("advisor_team_id") or team_id
        owner = next((t for t in teams if t.get("id") == strategic_team_id), teams[0])
        context = self._build_context(state, owner, config)
        role_plan = {}
        for role in ROLES:
            need = self._role_need(owner, role, context["composition"])
            role_players = sorted(
                [p for p in context["remaining"] if p["ruolo"] == role],
                key=self._absolute_value,
                reverse=True,
            )
            role_plan[role] = {
                "owned": int(context["composition"].get(role, 0) - need),
                "open": need,
                "available": len(role_players),
                "demand": context["scarcity"][role]["demand"],
                "supply": context["scarcity"][role]["supply"],
                "qualitativeSupply": context["scarcity"][role]["qualitativeSupply"],
                "scarcity": round(context["scarcity"][role]["ratio"], 3),
                "qualitativeScarcity": round(context["scarcity"][role]["qualitativeRatio"], 3),
                "tierSupply": context["scarcity"][role]["tierSupply"],
                "estimatedSpend": round(sum(_float(p["price_credits"]) for p in role_players[:need])),
            }
        return {
            "kind": "overview",
            "rolePlan": role_plan,
            "credits": _float(owner.get("credits")),
            "slotsOpen": sum(self._role_need(owner, role, context["composition"]) for role in ROLES),
            "marketConfidence": round(_float(context["market"].get("confidence")), 3),
            "myTeamId": owner.get("id"),
            "bidderIndependent": True,
        }
