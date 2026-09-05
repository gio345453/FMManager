from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json

import pandas as pd

from src.data.clean_sheets_data import get_clean_sheets
from src.data.defense_modifier import calculate_defense_lineup_bonus
from src.data.fixture_difficulty import get_fixture_calculator
from src.data.titolarita_loader import get_status, get_titolarita


def _load_formations() -> Dict[str, Dict[str, int]]:
    """Carica i moduli da configurazione, senza duplicarli nel codice."""
    candidates = [
        Path("data/config/lineup_settings.json"),
        Path(__file__).resolve().parents[3] / "data" / "config" / "lineup_settings.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            formations = payload.get("formations", {})
            if isinstance(formations, dict) and formations:
                normalized = {}
                for name, composition in formations.items():
                    if not isinstance(composition, dict):
                        continue
                    normalized[str(name)] = {
                        role: int(value) for role, value in composition.items()
                    }
                if normalized:
                    return normalized
        except (OSError, ValueError, TypeError):
            continue
    raise RuntimeError("Configurazione moduli non disponibile.")


FORMATIONS = _load_formations()


class LineupValidationError(ValueError):
    pass


class LineupCalendarError(RuntimeError):
    pass


class LineupService:
    def __init__(self, df_with_overall: pd.DataFrame, league_config=None):
        """
        Servizio unico per valutazione e selezione della formazione.

        Args:
            df_with_overall: DataFrame canonico dei giocatori.
            league_config: configurazione centralizzata della lega.
                            È opzionale per mantenere compatibilità
                            con eventuali chiamanti legacy. """
        if df_with_overall is None:
            raise ValueError("df_with_overall cannot be None")
        self.df = df_with_overall.copy()
        self.league_config = league_config
        self.fixture_calculator = get_fixture_calculator()

        # Usa formazioni da league_config se disponibile, altrimenti fallback a FORMATIONS
        if league_config is not None:
            self.formations = league_config.formations
        else:
            self.formations = FORMATIONS

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        if value is None or pd.isna(value):
            return default
        if isinstance(value, str):
            value = value.replace("↑", "").replace("↓", "").replace("→", "").replace("%", "").replace(",", ".").strip()
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _role(value: Any) -> str:
        return str(value or "").strip()[:1].upper()

    def resolve_matchday(self, local_date: date) -> Tuple[int, date, date, List[str]]:
        grouped: Dict[int, List[date]] = {}
        warnings: List[str] = []

        for match in self.fixture_calculator.calendario.get("matches", []):
            raw_date = match.get("date")
            teams = (str(match.get("home_team", "")).strip(), str(match.get("away_team", "")).strip())
            matchday = match.get("matchday")
            if not raw_date or not matchday or not all(teams) or any(team.lower() == "nan" for team in teams):
                continue
            try:
                match_date = date.fromisoformat(str(raw_date))
                matchday = int(matchday)
            except (TypeError, ValueError):
                continue
            grouped.setdefault(matchday, []).append(match_date)

        if not grouped:
            raise LineupCalendarError("Il calendario non contiene fixture con data e squadre valide.")

        windows = sorted((matchday, min(days), max(days)) for matchday, days in grouped.items())
        for matchday, start, end in windows:
            if start <= local_date <= end:
                return matchday, start, end, warnings

        upcoming = [(matchday, start, end) for matchday, start, end in windows if end >= local_date]
        if not upcoming:
            raise LineupCalendarError("Non è disponibile una prossima giornata con fixture datate nel calendario.")

        matchday, start, end = min(upcoming, key=lambda window: window[1])
        return matchday, start, end, warnings

    def _extract_roster_ids(self, roster: Dict[str, Any]) -> List[int]:
        slots = roster.get("roster") if isinstance(roster, dict) else None
        if not isinstance(slots, list):
            raise LineupValidationError("La rosa deve contenere un array roster.")

        ids: List[int] = []
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            player = slot.get("player")
            if not isinstance(player, dict) or player.get("id") is None:
                continue
            try:
                player_id = int(player["id"])
            except (TypeError, ValueError):
                continue
            if player_id not in ids:
                ids.append(player_id)
        if not ids:
            raise LineupValidationError("La rosa non contiene giocatori validi.")
        return ids

    @staticmethod
    def _base_play_probability(player_name: str) -> Tuple[float, str, str | None]:
        titolarita = get_titolarita(player_name)
        try:
            probability = max(0.0, min(1.0, float(str(titolarita).replace("%", "").strip()) / 100))
            return probability, f"Titolarità {probability * 100:.0f}%", None
        except (TypeError, ValueError):
            status = get_status(player_name)
            fallback = 0.65 if status == "Titolare" else 0.4 if status else 0.3
            return fallback, f"Titolarità non disponibile ({status or 'status assente'})", f"Titolarità non disponibile per {player_name}: applicata stima prudente."

    def evaluate_player(self, row: pd.Series, matchday: int, options: Dict[str, float]) -> Tuple[Dict[str, Any], List[str]]:
        player_id = int(row["Id"])
        name = str(row["Nome"])
        team = str(row["Squadra"])
        role = self._role(row.get("R"))
        warnings: List[str] = []
        fixture = self.fixture_calculator.get_fixture_for_team(team, matchday)
        modifiers = self.fixture_calculator.calculate_difficulty_modifiers(team, matchday, role)

        base_play, titolarita_reason, titolarita_warning = self._base_play_probability(name)
        if titolarita_warning:
            warnings.append(titolarita_warning)
        play_probability = min(1.0, base_play * modifiers["play_modifier"])
        mv = self._number(row.get("Mv_weighted"), 6.0)

        # NOTE: vote_modifier è un moltiplicatore percentuale (1.0 = neutrale, 1.035 = +3.5%)
        # Questo significa che giocatori forti guadagnano più punti assoluti con fixture facili.
        # Semanticamente potrebbe essere più corretto: mv + (vote_modifier - 1.0) * reference_mv
        # Ma manteniamo coerenza con sistema FisherTiger (moltiplicativo).
        projected_mv = max(4.0, min(10.0, mv * modifiers["vote_modifier"]))
        appearances = max(self._number(row.get("Pv_weighted"), 0.0), 1.0)
        goals_rate = self._number(row.get("Gf_weighted"), 0.0) / appearances
        assists_rate = self._number(row.get("Ass_weighted"), 0.0) / appearances
        bonus_rate = goals_rate * options["goal_bonus"] + assists_rate * options["assist_bonus"]
        projected_bonus = bonus_rate * modifiers["bonus_modifier"]

        clean_sheet = 0.0
        if role == "P":
            clean_sheets = get_clean_sheets(name)
            if clean_sheets:
                clean_sheet_rate = min(0.65, clean_sheets / max(appearances, 1.0))
                opponent_attack = max(0.0, 10.0 - modifiers.get("difficulty_score", 5.0)) / 10
                clean_sheet = clean_sheet_rate * (0.65 + opponent_attack * 0.35) * options["clean_sheet_bonus"]
            else:
                warnings.append(f"Clean sheet non disponibile per {name}: contributo impostato a zero.")

        overall = self._number(row.get("Overall"), 50.0)
        fm = self._number(row.get("Fm_weighted"), projected_mv)

        # WARNING: quality_adjustment è un'euristica non statisticamente derivata.
        # Usa Overall (rating generale) e FM (fantamedia con bonus) come proxy di qualità.
        # Rischio: FM contiene già i bonus storici, potrebbe correlare con projected_bonus
        # → possibile doppio conteggio di informazione.
        # Formula attuale: normalizza Overall (±0.18 max) e FM (±0.12 max).
        quality_adjustment = max(-0.18, min(0.18, (overall - 50) / 300)) + max(-0.12, min(0.12, (fm - 6) / 12))

        # FIX BUG MATEMATICO #1: quality_adjustment deve essere DENTRO play_probability
        # Se Q modifica il rendimento quando il giocatore gioca: E[S] = P(G) × (E[S|G] + Q)
        # Non: E[S] = P(G) × E[S|G] + Q (questo applica Q anche quando non gioca)
        expected_score = play_probability * (projected_mv + projected_bonus + clean_sheet + quality_adjustment)

        if fixture is None:
            warnings.append(f"Fixture non trovata per {team} alla giornata {matchday}: applicati valori neutrali.")

        reasons = [titolarita_reason]
        if fixture:
            reasons.append("Partita in casa" if fixture["is_home"] else "Partita in trasferta")
            reasons.append(f"Difficoltà {modifiers['difficulty_score']:.1f}/10 contro {fixture['opponent']}")
        if role in {"P", "D"} and mv >= 6.2:
            reasons.append("Buona MV utile al modificatore difesa")

        return {
            "id": player_id,
            "nome": name,
            "squadra": team,
            "ruolo": role,
            "overall": round(overall),
            "fm_weighted": round(fm, 2),
            "mv_weighted": round(mv, 2),
            "titolarita": round(base_play * 100, 1),
            "opponent": modifiers.get("opponent"),
            "is_home": modifiers.get("is_home"),
            "difficulty_score": round(modifiers["difficulty_score"], 1),
            "role_difficulty_score": round(modifiers.get("role_difficulty_score", modifiers["difficulty_score"]), 1),
            "opponent_attack": round(modifiers.get("opponent_attack", 5.0), 1),
            "opponent_defense": round(modifiers.get("opponent_defense", 5.0), 1),
            "play_probability": round(play_probability, 3),
            "projected_mv": round(projected_mv, 2),
            "projected_bonus": round(projected_bonus, 2),
            "projected_clean_sheet": round(clean_sheet, 2),
            "expected_score": round(expected_score, 2),
            "score_breakdown": {
                "play_probability": round(play_probability, 3),
                "projected_mv": round(projected_mv, 2),
                "projected_bonus": round(projected_bonus, 2),
                "projected_clean_sheet": round(clean_sheet, 2),
                "quality_adjustment": round(quality_adjustment, 2),
            },
            "reasons": reasons,
        }, warnings

    def evaluate_roster(self, local_date: date, roster: Dict[str, Any], options: Dict[str, float]) -> Dict[str, List[Dict[str, Any]]]:
        """Valuta tutti i giocatori della rosa per la giornata risolta."""
        matchday, _, _, _ = self.resolve_matchday(local_date)
        roster_ids = self._extract_roster_ids(roster)
        players = self.df[self.df["Id"].isin(roster_ids)]
        evaluated: Dict[str, List[Dict[str, Any]]] = {role: [] for role in {"P", "D", "C", "A"}}
        for _, row in players.iterrows():
            role = self._role(row.get("R"))
            if role not in evaluated:
                continue
            scored, _ = self.evaluate_player(row, matchday, options)
            evaluated[role].append(scored)
        return evaluated

    def select_lineup(self, evaluated: Dict[str, List[Dict[str, Any]]], formation: str) -> Dict[str, Any]:
        """Seleziona XI e panchina partendo esclusivamente dalle valutazioni comuni."""
        if formation not in self.formations:
            raise LineupValidationError("Modulo non supportato.")
        starters: List[Dict[str, Any]] = []
        missing_roles: List[str] = []
        for role, required in self.formations[formation].items():
            role_players = sorted(evaluated.get(role, []), key=lambda player: player["expected_score"], reverse=True)
            starters.extend(role_players[:required])
            if len(role_players) < required:
                missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")
        starter_ids = {player["id"] for player in starters}
        bench = sorted(
            [player for role_players in evaluated.values() for player in role_players if player["id"] not in starter_ids],
            key=lambda player: (player["ruolo"] != "P", -player["expected_score"]),
        )
        return {"starters": starters, "bench": bench, "missing_roles": missing_roles}

    def available_formations(self) -> List[str]:
        """Restituisce i moduli disponibili dall'istanza corrente."""
        return list(self.formations.keys())

    # Compatibilita' per eventuali chiamanti interni/test legacy.
    def _score_player(self, row: pd.Series, matchday: int, options: Dict[str, float]) -> Tuple[Dict[str, Any], List[str]]:
        return self.evaluate_player(row, matchday, options)

    def recommend_auto(self, local_date: date, roster: Dict[str, Any], options: Dict[str, float]) -> Dict[str, Any]:
        candidates = []
        for formation in self.formations:
            recommendation = self.recommend(local_date, formation, roster, options)
            starters = recommendation["selection"]["starters"]
            if len(starters) == 11:
                candidates.append(recommendation)

        if not candidates:
            fallback = self.recommend(local_date, next(iter(self.formations)), roster, options)
            fallback["warnings"].append("Nessun modulo è completabile con la rosa disponibile: mostrato il miglior tentativo in 3-4-3.")
            return fallback

        return max(candidates, key=lambda recommendation: recommendation["lineup_summary"]["expected_score"])

    def recommend(self, local_date: date, formation: str, roster: Dict[str, Any], options: Dict[str, float]) -> Dict[str, Any]:
        if formation not in self.formations:
            raise LineupValidationError("Modulo non supportato.")

        matchday, start_date, end_date, warnings = self.resolve_matchday(local_date)
        roster_ids = self._extract_roster_ids(roster)
        players = self.df[self.df["Id"].isin(roster_ids)]
        found_ids = {int(player_id) for player_id in players["Id"].tolist()}
        missing_ids = sorted(set(roster_ids) - found_ids)
        if missing_ids:
            warnings.append(f"{len(missing_ids)} giocatori della rosa non sono più presenti nel listone.")

        by_role: Dict[str, List[Dict[str, Any]]] = {role: [] for role in self.formations[formation]}
        missing_fixture = 0
        missing_titolarita = 0
        for _, row in players.iterrows():
            role = self._role(row.get("R"))
            if role not in by_role:
                continue
            scored, player_warnings = self.evaluate_player(row, matchday, options)
            by_role[role].append(scored)
            warnings.extend(player_warnings)
            missing_fixture += int(scored["opponent"] is None)
            missing_titolarita += int(any("Titolarità non disponibile" in warning for warning in player_warnings))

        # OTTIMIZZAZIONE ESATTA per difesa + portiere
        # Il defense_modifier dipende solo da P+D, quindi possiamo ottimizzare esattamente
        # quella parte senza esplodere computazionalmente.
        starters: List[Dict[str, Any]] = []
        missing_roles: List[str] = []

        # 1. Per C e A: selezione greedy (non hanno interazione collettiva)
        for role in ['C', 'A']:
            if role not in self.formations[formation]:
                continue
            required = self.formations[formation][role]
            role_players = sorted(by_role[role], key=lambda player: player["expected_score"], reverse=True)
            starters.extend(role_players[:required])
            if len(role_players) < required:
                missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        # 2. Per P+D: ottimizzazione esatta considerando defense_modifier
        from itertools import combinations

        required_p = self.formations[formation].get('P', 0)
        required_d = self.formations[formation].get('D', 0)

        available_p = by_role.get('P', [])
        available_d = by_role.get('D', [])

        if required_p > 0 and required_d > 0 and available_p and available_d:
            best_score = -float('inf')
            best_combo = None

            # Prova tutte le combinazioni P+D
            for p_combo in combinations(available_p, min(required_p, len(available_p))):
                for d_combo in combinations(available_d, min(required_d, len(available_d))):
                    # Calcola punteggio totale di questa combinazione
                    combo_players = list(p_combo) + list(d_combo)
                    individual_score = sum(player["expected_score"] for player in combo_players)

                    # Calcola defense_modifier per questa combinazione
                    goalkeeper = p_combo[0] if p_combo else None
                    defender_mvs = [player["projected_mv"] for player in d_combo]
                    defense_mod = calculate_defense_lineup_bonus(
                        goalkeeper["projected_mv"] if goalkeeper else None,
                        defender_mvs,
                    )

                    total = individual_score + defense_mod

                    if total > best_score:
                        best_score = total
                        best_combo = combo_players

            if best_combo:
                starters.extend(best_combo)
            else:
                # Fallback: greedy se nessuna combinazione valida
                if required_p > 0:
                    p_sorted = sorted(available_p, key=lambda p: p["expected_score"], reverse=True)
                    starters.extend(p_sorted[:required_p])
                if required_d > 0:
                    d_sorted = sorted(available_d, key=lambda p: p["expected_score"], reverse=True)
                    starters.extend(d_sorted[:required_d])
        else:
            # Fallback: greedy se manca P o D
            for role in ['P', 'D']:
                if role not in self.formations[formation]:
                    continue
                required = self.formations[formation][role]
                role_players = sorted(by_role[role], key=lambda player: player["expected_score"], reverse=True)
                starters.extend(role_players[:required])
                if len(role_players) < required:
                    missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        # Verifica missing per P e D
        if required_p > len(available_p):
            missing_roles.append(f"P: richiesti {required_p}, disponibili {len(available_p)}")
        if required_d > len(available_d):
            missing_roles.append(f"D: richiesti {required_d}, disponibili {len(available_d)}")
            if len(role_players) < required:
                missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        starter_ids = {player["id"] for player in starters}
        bench = sorted(
            [player for role_players in by_role.values() for player in role_players if player["id"] not in starter_ids],
            key=lambda player: (player["ruolo"] != "P", -player["expected_score"]),
        )
        if missing_roles:
            warnings.append("Rosa insufficiente per il modulo scelto: " + "; ".join(missing_roles) + ".")

        goalkeeper = next((player for player in starters if player["ruolo"] == "P"), None)
        defender_mvs = [player["projected_mv"] for player in starters if player["ruolo"] == "D"]
        defense_modifier = calculate_defense_lineup_bonus(
            goalkeeper["projected_mv"] if goalkeeper else None,
            defender_mvs,
        )
        expected_score = sum(player["expected_score"] for player in starters) + defense_modifier

        return {
            "matchday": matchday,
            "date_range": {"from": start_date.isoformat(), "to": end_date.isoformat()},
            "formation": formation,
            "selection": {"starters": starters, "bench": bench},
            "lineup_summary": {
                "expected_score": round(expected_score, 2),
                "expected_defense_modifier": defense_modifier,
                "coverage": {
                    "players_with_fixture": max(0, len(players) - missing_fixture),
                    "players_missing_fixture": missing_fixture,
                    "players_missing_titolarita": missing_titolarita,
                },
            },
            "warnings": list(dict.fromkeys(warnings)),
        }

    def recommend_for_matchday(self, matchday: int, formation: str, roster: Dict[str, Any], options: Dict[str, float]) -> Dict[str, Any]:
        """Variante che accetta matchday direttamente invece di risolvere local_date.

        Usata da MonteCarloLineupAdapter e test quando la giornata è già nota.
        """
        if formation not in self.formations:
            raise LineupValidationError("Modulo non supportato.")

        warnings: List[str] = []
        roster_ids = self._extract_roster_ids(roster)
        players = self.df[self.df["Id"].isin(roster_ids)]
        found_ids = {int(player_id) for player_id in players["Id"].tolist()}
        missing_ids = sorted(set(roster_ids) - found_ids)
        if missing_ids:
            warnings.append(f"{len(missing_ids)} giocatori della rosa non sono più presenti nel listone.")

        by_role: Dict[str, List[Dict[str, Any]]] = {role: [] for role in self.formations[formation]}
        missing_fixture = 0
        missing_titolarita = 0
        for _, row in players.iterrows():
            role = self._role(row.get("R"))
            if role not in by_role:
                continue
            scored, player_warnings = self.evaluate_player(row, matchday, options)
            by_role[role].append(scored)
            warnings.extend(player_warnings)
            missing_fixture += int(scored["opponent"] is None)
            missing_titolarita += int(any("Titolarità non disponibile" in warning for warning in player_warnings))

        # OTTIMIZZAZIONE ESATTA per difesa + portiere
        # Il defense_modifier dipende solo da P+D, quindi possiamo ottimizzare esattamente
        # quella parte senza esplodere computazionalmente.
        starters: List[Dict[str, Any]] = []
        missing_roles: List[str] = []

        # 1. Per C e A: selezione greedy (non hanno interazione collettiva)
        for role in ['C', 'A']:
            if role not in self.formations[formation]:
                continue
            required = self.formations[formation][role]
            role_players = sorted(by_role[role], key=lambda player: player["expected_score"], reverse=True)
            starters.extend(role_players[:required])
            if len(role_players) < required:
                missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        # 2. Per P+D: ottimizzazione esatta considerando defense_modifier
        from itertools import combinations

        required_p = self.formations[formation].get('P', 0)
        required_d = self.formations[formation].get('D', 0)

        available_p = by_role.get('P', [])
        available_d = by_role.get('D', [])

        if required_p > 0 and required_d > 0 and available_p and available_d:
            best_score = -float('inf')
            best_combo = None

            # Prova tutte le combinazioni P+D
            for p_combo in combinations(available_p, min(required_p, len(available_p))):
                for d_combo in combinations(available_d, min(required_d, len(available_d))):
                    # Calcola punteggio totale di questa combinazione
                    combo_players = list(p_combo) + list(d_combo)
                    individual_score = sum(player["expected_score"] for player in combo_players)

                    # Calcola defense_modifier per questa combinazione
                    goalkeeper = p_combo[0] if p_combo else None
                    defender_mvs = [player["projected_mv"] for player in d_combo]
                    defense_mod = calculate_defense_lineup_bonus(
                        goalkeeper["projected_mv"] if goalkeeper else None,
                        defender_mvs,
                    )

                    total = individual_score + defense_mod

                    if total > best_score:
                        best_score = total
                        best_combo = combo_players

            if best_combo:
                starters.extend(best_combo)
            else:
                # Fallback: greedy se nessuna combinazione valida
                if required_p > 0:
                    p_sorted = sorted(available_p, key=lambda p: p["expected_score"], reverse=True)
                    starters.extend(p_sorted[:required_p])
                if required_d > 0:
                    d_sorted = sorted(available_d, key=lambda p: p["expected_score"], reverse=True)
                    starters.extend(d_sorted[:required_d])
        else:
            # Fallback: greedy se manca P o D
            for role in ['P', 'D']:
                if role not in self.formations[formation]:
                    continue
                required = self.formations[formation][role]
                role_players = sorted(by_role[role], key=lambda player: player["expected_score"], reverse=True)
                starters.extend(role_players[:required])
                if len(role_players) < required:
                    missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        # Verifica missing per P e D
        if required_p > len(available_p):
            missing_roles.append(f"P: richiesti {required_p}, disponibili {len(available_p)}")
        if required_d > len(available_d):
            missing_roles.append(f"D: richiesti {required_d}, disponibili {len(available_d)}")
            if len(role_players) < required:
                missing_roles.append(f"{role}: richiesti {required}, disponibili {len(role_players)}")

        starter_ids = {player["id"] for player in starters}
        bench = sorted(
            [player for role_players in by_role.values() for player in role_players if player["id"] not in starter_ids],
            key=lambda player: (player["ruolo"] != "P", -player["expected_score"]),
        )
        if missing_roles:
            warnings.append("Rosa insufficiente per il modulo scelto: " + "; ".join(missing_roles) + ".")

        goalkeeper = next((player for player in starters if player["ruolo"] == "P"), None)
        defender_mvs = [player["projected_mv"] for player in starters if player["ruolo"] == "D"]
        defense_modifier = calculate_defense_lineup_bonus(
            goalkeeper["projected_mv"] if goalkeeper else None,
            defender_mvs,
        )
        expected_score = sum(player["expected_score"] for player in starters) + defense_modifier

        return {
            "matchday": matchday,
            "formation": formation,
            "selection": {"starters": starters, "bench": bench},
            "lineup_summary": {
                "expected_score": round(expected_score, 2),
                "expected_defense_modifier": defense_modifier,
                "coverage": {
                    "players_with_fixture": max(0, len(players) - missing_fixture),
                    "players_missing_fixture": missing_fixture,
                    "players_missing_titolarita": missing_titolarita,
                },
            },
            "warnings": list(dict.fromkeys(warnings)),
        }
