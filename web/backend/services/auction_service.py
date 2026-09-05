"""
Auction service - Fase 0 della modalità Asta Fishertiger.
Gestisce stato runtime, validazione, assegnazioni, storico e undo/redo.
Lo stato persistito è ricostruibile e non viene modificato direttamente dalla UI.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.data.league_config import LeagueConfig


ROLES = ("P", "D", "C", "A")
PHASES = ("NOT_STARTED", "ROLE_P", "ROLE_D", "ROLE_C", "ROLE_A", "FINISHED")
POLICIES = (
    "call",
    "call_by_role",
    "random",
    "random_by_role",
    "alphabetical",
    "alphabetical_by_role",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_role(value: Any) -> str:
    text = str(value or "").strip()
    return text.split("/")[0].split("(")[0].strip().upper()


class AuctionValidationError(ValueError):
    """Errore per un'operazione d'asta non valida."""


class AuctionService:
    def __init__(
        self,
        players_df: Optional[pd.DataFrame],
        state_path: Optional[str | Path] = None,
        league_config: Optional["LeagueConfig"] = None,
    ):
        self.players_df = players_df if players_df is not None else pd.DataFrame()
        self.state_path = Path(state_path or "data/user_data/auction_state.json")
        self.league_config = league_config
        self.state = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as fh:
                    state = json.load(fh)
                return self._normalize_loaded_state(state)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return self._empty_state()

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        with temp_path.open("w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=2, ensure_ascii=False)
        temp_path.replace(self.state_path)

    def _empty_state(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "phase": "NOT_STARTED",
            "rules": self._default_rules(),
            "teams": [],
            "assigned": {},
            "history": [],
            "redo": [],
            "current_auction": None,
            "updated_at": _now_iso(),
        }

    def _default_rules(self) -> Dict[str, Any]:
        # Se league_config è disponibile, usa roster_composition da lì
        # Altrimenti fallback al valore hardcoded per backward compatibility
        default_composition = {"P": 3, "D": 8, "C": 8, "A": 6}
        if self.league_config is not None:
            default_composition = dict(self.league_config.roster_composition)

        return {
            "participants": 10,
            "starting_credits": 500,
            "composition": default_composition,
            "minimum_price": 1,
            "bid_increment": 1,
            "reserve_per_slot": 1,
            "call_policy": "call",
        }

    def _normalize_loaded_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._empty_state()
        if not isinstance(state, dict):
            return normalized
        normalized.update({k: state.get(k, v) for k, v in normalized.items()})
        normalized["rules"] = {**self._default_rules(), **(state.get("rules") or {})}
        normalized["rules"]["composition"] = {
            **self._default_rules()["composition"],
            **(state.get("rules", {}).get("composition") or {}),
        }
        normalized["teams"] = list(state.get("teams") or [])
        normalized["assigned"] = dict(state.get("assigned") or {})
        normalized["history"] = list(state.get("history") or [])
        normalized["redo"] = list(state.get("redo") or [])
        normalized["current_auction"] = state.get("current_auction")
        normalized["phase"] = state.get("phase") if state.get("phase") in PHASES else "NOT_STARTED"
        return normalized

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def sync_league_config(self, league_config: Optional["LeagueConfig"]) -> None:
        """Sincronizza le regole dell'asta con le impostazioni correnti."""
        self.league_config = league_config
        if league_config is None:
            return
        rules = self.state.setdefault("rules", self._default_rules())
        old_starting_credits = int(rules.get("starting_credits") or round(league_config.starting_budget))
        new_starting_credits = int(round(league_config.starting_budget))
        rules["participants"] = int(league_config.participants)
        rules["starting_credits"] = new_starting_credits
        rules["composition"] = {
            role: int(league_config.roster_composition.get(role, 0)) for role in ROLES
        }
        rules["minimum_price"] = max(1, int(round(league_config.min_price)))
        rules["bid_increment"] = max(1, int(round(league_config.bid_increment)))
        rules["reserve_per_slot"] = max(0, int(round(league_config.reserve)))
        if self.state.get("teams"):
            for team in self.state["teams"]:
                spent = max(0, old_starting_credits - int(team.get("credits", old_starting_credits)))
                if not self.state.get("history") or old_starting_credits != new_starting_credits:
                    team["starting_credits"] = new_starting_credits
                    team["credits"] = max(0, new_starting_credits - spent)

    def get_state(self) -> Dict[str, Any]:
        return copy.deepcopy(self.state)

    def get_players(self) -> List[Dict[str, Any]]:
        if self.players_df is None or self.players_df.empty:
            return []
        assigned_ids = {int(pid) for pid in self.state["assigned"].keys()}
        current = self.state.get("current_auction") or {}
        active_id = current.get("player_id")
        budget = float(self.state.get("rules", {}).get("starting_credits", 500))
        calculator = getattr(self, "price_calculator", None)
        results = []
        for _, row in self.players_df.iterrows():
            pid = int(row["Id"])
            role = _base_role(row.get("R"))
            if role not in ROLES:
                continue
            price_percentage = None
            price_credits = None
            if calculator is not None:
                try:
                    pdata = calculator.calculate_price_percentage(pid, budget)
                    price_percentage = self._clean_float(pdata.get("percentage"))
                    price_credits = self._clean_float(pdata.get("credits"))
                except Exception:
                    pass
            results.append({
                "id": pid,
                "nome": str(row.get("Nome", "")),
                "squadra": str(row.get("Squadra", "")),
                "ruolo": role,
                "overall": self._clean_int(row.get("Overall")),
                "fvm": self._clean_float(row.get("FVM")),
                "price_percentage": price_percentage,
                "price_credits": price_credits,
                "assigned": pid in assigned_ids,
                "current_auction": pid == active_id,
            })
        return results

    @staticmethod
    def _clean_int(value: Any) -> Optional[int]:
        try:
            if value is None or pd.isna(value):
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clean_float(value: Any) -> Optional[float]:
        try:
            if value is None or pd.isna(value):
                return None
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None

    def _find_player(self, player_id: int) -> Dict[str, Any]:
        if self.players_df is None or self.players_df.empty:
            raise AuctionValidationError("Dataset giocatori non disponibile.")
        rows = self.players_df[self.players_df["Id"] == player_id]
        if rows.empty:
            raise AuctionValidationError(f"Il giocatore {player_id} non esiste nel dataset corrente.")
        row = rows.iloc[0]
        role = _base_role(row.get("R"))
        if role not in ROLES:
            raise AuctionValidationError(f"Ruolo non valido per il giocatore {player_id}.")
        return {
            "id": int(row["Id"]),
            "nome": str(row.get("Nome", "")),
            "squadra": str(row.get("Squadra", "")),
            "ruolo": role,
        }

    def _team(self, team_id: str) -> Dict[str, Any]:
        for team in self.state["teams"]:
            if team["id"] == team_id:
                return team
        raise AuctionValidationError(f"Squadra '{team_id}' non trovata.")

    def _team_roster_count(self, team: Dict[str, Any], role: Optional[str] = None) -> int:
        if role is None:
            return len(team.get("roster", []))
        return sum(1 for item in team.get("roster", []) if item.get("role") == role)

    def _slots_remaining(self, team: Dict[str, Any], role: Optional[str] = None) -> int:
        composition = self.state["rules"]["composition"]
        if role:
            return max(0, int(composition.get(role, 0)) - self._team_roster_count(team, role))
        total = sum(int(v) for v in composition.values())
        return max(0, total - self._team_roster_count(team))

    def _legal_max_bid(self, team: Dict[str, Any]) -> int:
        open_slots = self._slots_remaining(team)
        reserve = int(self.state["rules"].get("reserve_per_slot", 1))
        reserve_need = max(0, open_slots - 1) * reserve
        spendable = max(0, int(team["credits"]) - reserve_need)
        increment = max(1, int(self.state["rules"].get("bid_increment", 1)))
        return (spendable // increment) * increment

    def _all_rosters_complete(self) -> bool:
        if not self.state["teams"]:
            return False
        return all(self._slots_remaining(team) == 0 for team in self.state["teams"])

    def _derive_phase(self) -> str:
        teams = self.state["teams"]
        if not teams:
            return "NOT_STARTED"
        if self._all_rosters_complete():
            return "FINISHED"

        policy = self.state["rules"].get("call_policy", "call")
        if "by_role" not in policy:
            return self.state.get("phase", "NOT_STARTED") if self.state.get("phase") not in ("NOT_STARTED", "FINISHED") else "ROLE_P"

        for role in ROLES:
            if any(self._slots_remaining(team, role) > 0 for team in teams):
                return f"ROLE_{role}"
        return "FINISHED"

    def _snapshot(self) -> Dict[str, Any]:
        return {
            "phase": self.state["phase"],
            "teams": copy.deepcopy(self.state["teams"]),
            "assigned": copy.deepcopy(self.state["assigned"]),
            "current_auction": copy.deepcopy(self.state.get("current_auction")),
        }

    def _record_transaction(self, action: str, before: Dict[str, Any], payload: Dict[str, Any]) -> None:
        self.state["history"].append(
            {
                "event_id": len(self.state["history"]) + 1,
                "timestamp": _now_iso(),
                "action": action,
                "payload": copy.deepcopy(payload),
                "before": before,
                "after": self._snapshot(),
            }
        )
        self.state["redo"] = []
        self.state["updated_at"] = _now_iso()
        self._save()

    def _apply_snapshot(self, snapshot: Dict[str, Any]) -> None:
        self.state["phase"] = snapshot["phase"]
        self.state["teams"] = copy.deepcopy(snapshot["teams"])
        self.state["assigned"] = copy.deepcopy(snapshot["assigned"])
        self.state["current_auction"] = copy.deepcopy(snapshot["current_auction"])
        self.state["updated_at"] = _now_iso()

    # ------------------------------------------------------------------
    # Setup / auction actions
    # ------------------------------------------------------------------
    def initialize(
        self,
        team_names: List[str],
        starting_credits: int = 500,
        composition: Optional[Dict[str, int]] = None,
        minimum_price: int = 1,
        bid_increment: int = 1,
        reserve_per_slot: int = 1,
        call_policy: str = "call",
    ) -> Dict[str, Any]:
        if not team_names:
            raise AuctionValidationError("È necessaria almeno una squadra.")
        if len(team_names) > 20:
            raise AuctionValidationError("Sono supportate al massimo 20 squadre.")
        names = [str(name).strip() for name in team_names if str(name).strip()]
        if len(set(names)) != len(names):
            raise AuctionValidationError("I nomi delle squadre devono essere univoci.")
        if starting_credits < 1:
            raise AuctionValidationError("I crediti iniziali devono essere positivi.")

        # Se composition non è fornita, usa league_config se disponibile, altrimenti fallback
        if composition is None:
            if self.league_config is not None:
                composition = dict(self.league_config.roster_composition)
            else:
                composition = {"P": 3, "D": 8, "C": 8, "A": 6}

        if any(role not in ROLES or int(slots) < 0 for role, slots in composition.items()):
            raise AuctionValidationError("Composizione rosa non valida.")
        if set(composition) != set(ROLES):
            raise AuctionValidationError("La composizione deve contenere P, D, C e A.")
        if minimum_price < 1 or bid_increment < 1 or reserve_per_slot < 0:
            raise AuctionValidationError("Minimo, incremento e riserva non sono validi.")
        if call_policy not in POLICIES:
            raise AuctionValidationError(f"Policy non valida: {call_policy}.")

        self.state = {
            "version": 1,
            "phase": "NOT_STARTED",
            "rules": {
                "participants": len(names),
                "starting_credits": int(starting_credits),
                "composition": {r: int(composition[r]) for r in ROLES},
                "minimum_price": int(minimum_price),
                "bid_increment": int(bid_increment),
                "reserve_per_slot": int(reserve_per_slot),
                "call_policy": call_policy,
            },
            "teams": [
                {
                    "id": f"team_{idx + 1}",
                    "name": name,
                    "starting_credits": int(starting_credits),
                    "credits": int(starting_credits),
                    "roster": [],
                }
                for idx, name in enumerate(names)
            ],
            "assigned": {},
            "history": [],
            "redo": [],
            "current_auction": None,
            "updated_at": _now_iso(),
        }
        self._save()
        return self.get_state()

    def set_phase(self, phase: str) -> Dict[str, Any]:
        if phase not in PHASES:
            raise AuctionValidationError(f"Fase non valida: {phase}")
        before = self._snapshot()
        self.state["phase"] = phase
        self._record_transaction("set_phase", before, {"phase": phase})
        return self.get_state()

    def start_auction(self) -> Dict[str, Any]:
        if not self.state["teams"]:
            raise AuctionValidationError("Configura prima le squadre.")
        before = self._snapshot()
        self.state["phase"] = self._derive_phase()
        if self.state["phase"] == "NOT_STARTED":
            self.state["phase"] = "ROLE_P"
        self._record_transaction("start", before, {})
        return self.get_state()

    def open_player(self, player_id: int) -> Dict[str, Any]:
        player = self._find_player(int(player_id))
        if str(player_id) in self.state["assigned"]:
            raise AuctionValidationError("Il giocatore è già assegnato.")
        policy = self.state["rules"].get("call_policy", "call")
        phase = self.state.get("phase", "NOT_STARTED")
        if policy.endswith("_by_role") and phase.startswith("ROLE_") and phase[-1] in ROLES and player["ruolo"] != phase[-1]:
            raise AuctionValidationError(f"La fase corrente è {phase}: il giocatore deve essere di ruolo {phase[-1]}.")
        minimum = int(self.state["rules"]["minimum_price"])
        before = self._snapshot()
        self.state["current_auction"] = {
            "player_id": player["id"],
            "role": player["ruolo"],
            "opening_price": minimum,
            "current_price": minimum,
            "last_bidder": None,
            "opened_at": _now_iso(),
        }
        self._record_transaction("open_player", before, {"player_id": player_id})
        return self.get_state()

    def place_bid(self, team_id: str, price: int) -> Dict[str, Any]:
        current = self.state.get("current_auction")
        if not current:
            raise AuctionValidationError("Nessun giocatore attualmente in asta.")
        team = self._team(team_id)
        player = self._find_player(int(current["player_id"]))
        if str(player["id"]) in self.state["assigned"]:
            raise AuctionValidationError("Il giocatore è già assegnato.")
        if self._slots_remaining(team, player["ruolo"]) <= 0:
            raise AuctionValidationError(f"{team['name']} non ha slot disponibili per il ruolo {player['ruolo']}.")
        minimum = int(self.state["rules"]["minimum_price"])
        increment = max(1, int(self.state["rules"]["bid_increment"]))
        previous = int(current["current_price"])
        required = minimum if current["last_bidder"] is None else previous + increment
        if int(price) < required:
            raise AuctionValidationError(f"Il bid deve essere almeno {required}.")
        if (int(price) - required) % increment != 0:
            raise AuctionValidationError(f"Il bid deve rispettare l'incremento di {increment}.")
        legal_max = self._legal_max_bid(team)
        if int(price) > legal_max:
            raise AuctionValidationError(f"Bid non consentito: legal max di {team['name']} = {legal_max}.")

        before = self._snapshot()
        current["current_price"] = int(price)
        current["last_bidder"] = team_id
        current["last_bid_at"] = _now_iso()
        self._record_transaction("bid", before, {"team_id": team_id, "price": int(price), "player_id": player["id"]})
        return self.get_state()

    def assign_current(self) -> Dict[str, Any]:
        current = self.state.get("current_auction")
        if not current:
            raise AuctionValidationError("Nessun giocatore in asta.")
        winner_id = current.get("last_bidder")
        if not winner_id:
            raise AuctionValidationError("Il giocatore non ha ancora un'offerta valida.")
        team = self._team(winner_id)
        player = self._find_player(int(current["player_id"]))
        player_key = str(player["id"])
        if player_key in self.state["assigned"]:
            raise AuctionValidationError("Il giocatore è già assegnato.")
        price = int(current["current_price"])
        role = player["ruolo"]
        if self._slots_remaining(team, role) <= 0:
            raise AuctionValidationError(f"{team['name']} non ha slot disponibili per {role}.")
        if price > self._legal_max_bid(team):
            raise AuctionValidationError("L'assegnazione supererebbe il legal max.")

        before = self._snapshot()
        team["credits"] -= price
        roster_item = {
            "player_id": player["id"],
            "name": player["nome"],
            "role": role,
            "team": player["squadra"],
            "price": price,
        }
        team["roster"].append(roster_item)
        self.state["assigned"][player_key] = {
            "owner": winner_id,
            "owner_name": team["name"],
            "price": price,
            "role": role,
            "player_name": player["nome"],
        }
        self.state["current_auction"] = None
        self.state["phase"] = self._derive_phase()
        self._record_transaction(
            "assign",
            before,
            {"team_id": winner_id, "player_id": player["id"], "price": price},
        )
        return self.get_state()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------
    def undo(self) -> Dict[str, Any]:
        if not self.state["history"]:
            raise AuctionValidationError("Nessuna operazione da annullare.")
        event = self.state["history"].pop()
        self.state["redo"].append(event)
        self._apply_snapshot(event["before"])
        self._save()
        return self.get_state()

    def redo(self) -> Dict[str, Any]:
        if not self.state["redo"]:
            raise AuctionValidationError("Nessuna operazione da ripristinare.")
        event = self.state["redo"].pop()
        # Revalida gli elementi mutabili prima di applicare il redo.
        self._validate_snapshot(event["after"])
        self._apply_snapshot(event["after"])
        self.state["history"].append(event)
        self._save()
        return self.get_state()

    def _validate_snapshot(self, snapshot: Dict[str, Any]) -> None:
        # Budget e slot devono rimanere non negativi/coerenti.
        composition = self.state["rules"]["composition"]
        total_slots = sum(int(v) for v in composition.values())
        for team in snapshot.get("teams", []):
            if team.get("credits", 0) < 0:
                raise AuctionValidationError("Redo non applicabile: crediti negativi.")
            if len(team.get("roster", [])) > total_slots:
                raise AuctionValidationError("Redo non applicabile: rosa oltre gli slot.")
            for role in ROLES:
                if self._count_snapshot_role(team, role) > int(composition.get(role, 0)):
                    raise AuctionValidationError(f"Redo non applicabile: slot {role} superati.")

    @staticmethod
    def _count_snapshot_role(team: Dict[str, Any], role: str) -> int:
        return sum(1 for item in team.get("roster", []) if item.get("role") == role)

    def reset(self) -> Dict[str, Any]:
        self.state = self._empty_state()
        self._save()
        return self.get_state()

    def get_team_summaries(self) -> List[Dict[str, Any]]:
        result = []
        for team in self.state["teams"]:
            slots = {role: self._slots_remaining(team, role) for role in ROLES}
            result.append(
                {
                    "id": team["id"],
                    "name": team["name"],
                    "starting_credits": team["starting_credits"],
                    "credits": team["credits"],
                    "roster_count": len(team.get("roster", [])),
                    "slots_remaining": slots,
                    "legal_max_bid": self._legal_max_bid(team),
                }
            )
        return result
