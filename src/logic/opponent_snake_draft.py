"""Generazione rose avversarie: Snake Draft con budget realmente spendibile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

import numpy as np

from src.data.league_config import LeagueConfig


@dataclass
class OpponentDraftState:
    team: str
    remaining_budget: float
    remaining_slots: Dict[str, int]
    aggressiveness: float
    roster: List[Dict[str, Any]] = field(default_factory=list)
    spent: float = 0.0

    @property
    def slots_remaining(self) -> int:
        return sum(self.remaining_slots.values())


class BudgetAwareSnakeDraft:
    """Assegna giocatori senza rendere impossibile il completamento della rosa."""

    def __init__(self, config: LeagueConfig, rng: np.random.Generator, allow_budget_overflow: bool = True):
        self.config = config
        self.rng = rng
        self.allow_budget_overflow = allow_budget_overflow
        self.last_audit: Dict[str, Dict[str, float]] = {}

        # Cache deterministic values used repeatedly during the draft.
        self._price_floor_cache: Dict[Any, float] = {}
        self._quality_cache: Dict[Any, float] = {}
        self._sorted_role_pools: Dict[str, List[Dict[str, Any]]] = {}

    def auction_value(self, player: Dict[str, Any]) -> float:
        """Auction Value ufficiale: price_percentage applicato al budget di lega."""
        try:
            percentage = float(player.get("price_percentage", 0) or 0)
        except (TypeError, ValueError):
            percentage = 0.0
        return max(self.config.min_price, round(self.config.starting_budget * percentage / 100.0, 2))

    @staticmethod
    def _titolarita(player: Dict[str, Any]) -> float:
        """Estrae la titolarità come float 0.0-1.0"""
        titolarita = player.get("titolarita")
        if titolarita is None:
            return 0.5  # default neutrale
        try:
            if isinstance(titolarita, str):
                return float(titolarita.replace("%", "").strip()) / 100.0
            return float(titolarita) / 100.0 if float(titolarita) > 1.0 else float(titolarita)
        except (TypeError, ValueError):
            return 0.5

    @staticmethod
    def _quality(player: Dict[str, Any]) -> float:
        """Qualità base + boost per titolarità se portiere"""
        base_quality = 0.0
        for key in ("fm_weighted", "overall", "mv_weighted"):
            try:
                base_quality = float(player.get(key, 0) or 0)
                if base_quality > 0:
                    break
            except (TypeError, ValueError):
                pass

        # Per i portieri, penalizza fortemente le riserve
        ruolo = str(player.get("ruolo", "")).strip().upper()
        if ruolo == "P":
            titolarita = BudgetAwareSnakeDraft._titolarita(player)
            # Un portiere titolare (0.8+) vale molto di più in draft
            # Un portiere riserva (0.3-) deve essere evitato
            titolarita_boost = (titolarita - 0.5) * 15.0  # Range: -7.5 a +7.5
            return base_quality + titolarita_boost

        return base_quality

    def _quality_cached(self, player: Dict[str, Any]) -> float:
        player_id = player.get("id")
        cache_key = player_id if player_id is not None else id(player)
        cached = self._quality_cache.get(cache_key)
        if cached is not None:
            return cached
        value = self._quality(player)
        self._quality_cache[cache_key] = value
        return value

    def _price_floor(self, player: Dict[str, Any]) -> float:
        """Un top non può essere assegnato al prezzo simbolico di 1-2 crediti."""
        player_id = player.get("id")
        cache_key = player_id if player_id is not None else id(player)
        cached = self._price_floor_cache.get(cache_key)
        if cached is not None:
            return cached
        value = max(self.config.min_price, float(np.ceil(self.auction_value(player) * 0.65)))
        self._price_floor_cache[cache_key] = value
        return value

    def _minimum_completion_cost(
        self,
        remaining_slots: Dict[str, int],
        pool_by_role: Dict[str, List[Dict[str, Any]]],
        used_ids: set,
    ) -> float:
        """Costo minimo reale per ruolo calcolato senza riordinare il listone a ogni candidato.

        La matematica è identica alla versione precedente: per ogni ruolo vengono
        presi i ``slots`` price-floor più bassi tra i giocatori non ancora usati.
        I pool sono ordinati una sola volta per ruolo e qui si attraversano solo
        i primi elementi necessari, saltando quelli già assegnati.

        Con allow_budget_overflow=True, restituisce il costo reale anche se supera
        il budget, permettendo al draft di continuare con sforamento controllato.
        """
        cost = self.config.reserve
        for role, slots in remaining_slots.items():
            if slots <= 0:
                continue

            sorted_pool = self._sorted_role_pools.get(role)
            if sorted_pool is None:
                sorted_pool = sorted(pool_by_role[role], key=self._price_floor)
                self._sorted_role_pools[role] = sorted_pool

            found = 0
            role_cost = 0.0
            for player in sorted_pool:
                if player["id"] in used_ids:
                    continue
                role_cost += self._price_floor(player)
                found += 1
                if found == slots:
                    break

            if found < slots:
                if self.allow_budget_overflow:
                    # Con overflow permesso, continua comunque usando il costo parziale
                    # invece di bloccare completamente il draft
                    pass
                else:
                    return float("inf")
            cost += role_cost
        return cost

    def _next_role(self, state: OpponentDraftState) -> str:
        # Prima completa le esigenze più urgenti, mantenendo la composizione.
        return max(
            (role for role, slots in state.remaining_slots.items() if slots > 0),
            key=lambda role: state.remaining_slots[role] / self.config.roster_composition[role],
        )

    def _simulated_price(self, player: Dict[str, Any], max_spend: float, state: OpponentDraftState) -> float:
        # Prezzo di mercato casuale: l'aggressività rende più probabile pagare sopra AV.
        auction_value = self.auction_value(player)
        market_factor = max(0.55, self.rng.normal(1.0 + state.aggressiveness, 0.12))
        proposed = max(self._price_floor(player), round(auction_value * market_factor))

        # Se siamo nelle ultime scelte e allow_budget_overflow è attivo,
        # permetti di pagare oltre il max_spend teorico
        if self.allow_budget_overflow and state.slots_remaining <= 5:
            # Nelle ultime 5 scelte, permetti sforamento controllato
            max_overflow = self.config.starting_budget * 0.2
            adjusted_max_spend = max_spend + max_overflow
            return min(proposed, round(adjusted_max_spend))

        return min(proposed, round(max_spend))

    def _choose_player(
        self,
        candidates: List[Dict[str, Any]],
        state: OpponentDraftState,
        pool_by_role: Dict[str, List[Dict[str, Any]]],
        used_ids: set,
    ) -> Dict[str, Any] | None:
        if not candidates:
            return None

        # Calcola sforamento massimo permesso (20% del budget iniziale)
        max_overflow = self.config.starting_budget * 0.2 if self.allow_budget_overflow else 0.0

        feasible = []
        for player in candidates:
            next_slots = dict(state.remaining_slots)
            next_slots[str(player["ruolo"]).strip()[:1].upper()] -= 1
            min_remaining = self._minimum_completion_cost(next_slots, pool_by_role, used_ids | {player["id"]})

            # Budget check con tolleranza per overflow
            budget_available = state.remaining_budget + max_overflow
            if self._price_floor(player) + min_remaining <= budget_available + 1e-9:
                feasible.append(player)

        pool = feasible
        if not pool:
            # Se nessun giocatore è "feasible" con il budget standard, ma allow_budget_overflow è True,
            # prendi comunque i candidati disponibili (fallback per completare la rosa)
            if self.allow_budget_overflow:
                # Fallback attivo: ignora vincoli di budget e prendi dai candidati disponibili
                pool = candidates
                if pool:
                    print(f"  [Draft Overflow] Attivato fallback: {len(pool)} candidati ignorano vincoli budget (slots rimasti: {state.slots_remaining})")
            else:
                return None

        if not pool:
            return None

        qualities = np.asarray([self._quality_cached(player) for player in pool], dtype=float)
        # Le squadre con budget residuo alto possono trasformare i risparmi in qualità.
        pressure = max(0.1, state.remaining_budget / self.config.starting_budget)
        weights = np.exp((qualities - qualities.max()) * (1.0 + pressure + state.aggressiveness))
        weights /= weights.sum()
        return pool[int(self.rng.choice(len(pool), p=weights))]

    def draft(self, players: Iterable[Dict[str, Any]], teams: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        pool_by_role: Dict[str, List[Dict[str, Any]]] = {role: [] for role in self.config.roster_composition}
        for raw_player in players:
            role = str(raw_player.get("ruolo", "")).strip()[:1].upper()
            if role in pool_by_role and raw_player.get("id") is not None:
                pool_by_role[role].append(dict(raw_player))

        # I pool ordinati sono validi per questo draft e vengono ricostruiti
        # all'inizio di ogni nuova generazione di rose.
        self._sorted_role_pools = {
            role: sorted(role_players, key=self._price_floor)
            for role, role_players in pool_by_role.items()
        }

        # Arricchisci con titolarità se non presente
        from src.data.titolarita_loader import get_titolarita
        for role_players in pool_by_role.values():
            for player in role_players:
                if "titolarita" not in player or player["titolarita"] is None:
                    nome = player.get("nome", "")
                    if nome:
                        tit_str = get_titolarita(nome)
                        if tit_str != "-":
                            try:
                                player["titolarita"] = float(tit_str.replace("%", "").strip())
                            except (ValueError, AttributeError):
                                player["titolarita"] = 50.0  # default neutrale
                        else:
                            player["titolarita"] = 50.0  # default neutrale
        states = {
            team: OpponentDraftState(
                team=team,
                remaining_budget=self.config.starting_budget,
                remaining_slots=dict(self.config.roster_composition),
                aggressiveness=float(self.rng.uniform(-0.08, 0.14)),
            )
            for team in teams
        }
        used_ids = set()
        total_rounds = sum(self.config.roster_composition.values())
        for round_index in range(total_rounds):
            order = teams if round_index % 2 == 0 else list(reversed(teams))
            for team in order:
                state = states[team]
                role = self._next_role(state)
                candidates = [player for player in pool_by_role[role] if player["id"] not in used_ids]
                chosen = self._choose_player(candidates, state, pool_by_role, used_ids)
                if chosen is None:
                    if self.allow_budget_overflow:
                        # Con budget overflow attivo, prova a prendere qualsiasi giocatore disponibile
                        # anche se il budget non è sufficiente
                        if candidates:
                            # Prendi il giocatore più economico tra i candidates disponibili
                            chosen = min(candidates, key=self._price_floor)
                            print(f"  [Draft Overflow] {team} - {role}: preso {chosen.get('nome')} (fallback economico)")
                        else:
                            # Nessun giocatore disponibile per questo ruolo
                            available_count = len([p for p in pool_by_role[role] if p["id"] not in used_ids])
                            total_count = len(pool_by_role[role])
                            raise ValueError(
                                f"Nessun giocatore disponibile per il ruolo {role} di {team}. "
                                f"Disponibili: {available_count}/{total_count}, già usati: {len(used_ids)}"
                            )
                    else:
                        raise ValueError(f"Offerta insufficiente per completare il ruolo {role} di {team}")
                auction_value = self.auction_value(chosen)
                next_slots = dict(state.remaining_slots)
                next_slots[role] -= 1
                minimum_remaining = self._minimum_completion_cost(next_slots, pool_by_role, used_ids | {chosen["id"]})
                max_spend = state.remaining_budget - minimum_remaining

                price = self._simulated_price(chosen, max_spend, state)

                # Con budget overflow, rilassa la validazione del vincolo
                if self.allow_budget_overflow:
                    # Permetti sforamento fino al 20% del budget iniziale
                    max_overflow = self.config.starting_budget * 0.2
                    if price < self._price_floor(chosen):
                        price = self._price_floor(chosen)
                    # Non lanciare errore se sforeremmo, accetta il prezzo calcolato
                else:
                    # Modalità strict: validazione rigida del budget
                    if price < self._price_floor(chosen) or price + minimum_remaining > state.remaining_budget + 1e-9:
                        raise RuntimeError("Snake Draft ha violato il vincolo di completamento")
                drafted = dict(chosen)
                drafted.update({
                    "auction_value_percentage": float(chosen.get("price_percentage", 0) or 0),
                    "auction_value_credits": auction_value,
                    "simulated_price": price,
                    "theoretical_value": auction_value,
                    "actual_spent": price,
                    "surplus": round(auction_value - price, 2),
                    "efficiency": round(self._quality_cached(chosen) / price, 4) if price else 0.0,
                })
                state.roster.append(drafted)
                state.spent += price
                state.remaining_budget -= price
                state.remaining_slots[role] -= 1
                used_ids.add(chosen["id"])
        self.last_audit = {
            team: {
                "theoretical_value": round(sum(player["theoretical_value"] for player in state.roster), 2),
                "actual_spent": round(state.spent, 2),
                "surplus": round(sum(player["surplus"] for player in state.roster), 2),
                "efficiency": round(sum(player["efficiency"] for player in state.roster) / len(state.roster), 4),
                "budget_remaining": round(state.remaining_budget, 2),
            }
            for team, state in states.items()
        }
        return {team: states[team].roster for team in teams}
