import unicodedata
import logging
import os
"""
Monte Carlo Simulator V4 - Modello avversari + lineup pre-match

Simula una stagione completa considerando:
- Rosa utente reale (da CompletaRosa)
- Rose avversarie generate automaticamente (snake draft)
- Disponibilità giocatori (status blend)
- Voti (Normal distribution)
- Eventi (Poisson: gol, assist, amm, esp, autogol)
- Clean sheet portieri
- Fixture difficulty (calendario Serie A)
- Bonus/malus configurabili utente
- Head-to-head completi
- Probabilità posizioni classifica finale
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Manager
from functools import lru_cache
from src.data.league_config import LeagueConfig
from src.logic.monte_carlo_lineup_adapter import MonteCarloLineupAdapter
from src.logic.opponent_snake_draft import BudgetAwareSnakeDraft


def _run_scenario_in_process(config: Dict) -> Dict:
    """
    Funzione top-level serializzabile per ProcessPoolExecutor.

    Ricrea il simulatore da zero nel processo figlio e esegue uno scenario.
    Invia progresso tramite queue per comunicazione inter-processo.

    Args:
        config: Dict con tutti i parametri serializzabili:
            - settings_dict: LeagueSettings come dict
            - root_path: Path come stringa
            - scenario_id: int
            - my_team: str
            - my_roster: List[dict]
            - opponent_rosters: Dict[str, List[dict]]
            - formation: str
            - league_calendar: dict
            - n_simulations: int
            - progress_queue: multiprocessing.Queue (opzionale)

    Returns:
        Dict con risultati scenario (serializzabile)
    """
    # 1. Ricrea LeagueSettings da dict
    settings = LeagueSettings(**config['settings_dict'])

    # 2. Ricrea simulatore nel processo figlio.
    # I dati statici gia' caricati dal processo principale vengono passati
    # serializzati nel config per evitare una nuova lettura dei CSV su disco.
    league_config = LeagueConfig(**config.get('league_config_dict', {}))
    simulator = MonteCarloSimulator(
        settings=settings,
        root_path=Path(config['root_path']),
        league_config=league_config,
        preloaded_team_strength=config.get('preloaded_team_strength'),
        preloaded_calendar_records=config.get('preloaded_calendar_records'),
    )

    # 3. Crea callback che invia progresso alla queue
    progress_queue = config.get('progress_queue')

    def progress_callback_with_queue(scenario_id, completed, total, progress_pct):
        if progress_queue is not None:
            try:
                progress_queue.put({
                    'scenario_id': scenario_id,
                    'completed': completed,
                    'total': total,
                    'progress': progress_pct
                })
            except Exception:
                pass  # Ignora errori di comunicazione

    print(f"[Processo {config['scenario_id']}] Avvio scenario...")

    result = simulator._simulate_season_scenario(
        my_team=config['my_team'],
        my_roster=config['my_roster'],
        opponent_rosters=config['opponent_rosters'],
        formation=config['formation'],
        league_calendar=config['league_calendar'],
        n_simulations=config['n_simulations'],
        scenario_id=config['scenario_id'],
        progress_callback=progress_callback_with_queue if progress_queue else None
    )

    print(f"[Processo {config['scenario_id']}] Scenario completato!")

    result['draft_audit'] = config.get('draft_audit', {})
    return result



def _json_safe(value):
    """Converte tipi NumPy/Pandas in tipi JSON serializzabili da FastAPI."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    return value


@dataclass
class _SimulationLog:
    """Compatibilità mantenuta: il simulatore non salva più i log su file."""

    def __init__(self, log_dir="simulation_logs"):
        self.log_dir = Path(log_dir)
        self._original_stdout = None
        self._original_stderr = None

    def start(self):
        return

    def stop(self):
        return


@dataclass
class LeagueSettings:
    """Impostazioni lega configurabili da utente"""
    # Bonus e Malus
    goal_bonus: float = 3.0
    assist_bonus: float = 1.0
    yellow_card_malus: float = 0.5
    red_card_malus: float = 1.0
    own_goal_malus: float = 2.0

    # Fasce Gol - PERSONALIZZABILI
    goal_threshold: int = 66  # Soglia primo gol virtuale (da che punteggio parte il primo gol)
    points_per_goal: int = 4  # Punti ogni gol virtuale successivo

    # Opzioni
    mvp_bonus_enabled: bool = True  # Bonus +1 punto al miglior giocatore della giornata
    clean_sheet_enabled: bool = False
    clean_sheet_bonus: float = 1.0
    defense_modifier_enabled: bool = True

    @classmethod
    def from_league_config(
        cls,
        config: LeagueConfig,
        overrides: Optional[Dict] = None,
    ) -> "LeagueSettings":
        """Adatta il contratto unico della lega al simulatore stagionale.

        Gli override servono esclusivamente alla richiesta corrente: non
        diventano una seconda fonte persistita di configurazione.
        """
        values = dict(config.scoring)
        values.update(overrides or {})
        return cls(
            goal_bonus=float(values["goal_bonus"]),
            assist_bonus=float(values["assist_bonus"]),
            yellow_card_malus=float(values["yellow_card_malus"]),
            red_card_malus=float(values["red_card_malus"]),
            own_goal_malus=float(values["own_goal_malus"]),
            goal_threshold=int(values["goal_threshold"]),
            points_per_goal=int(values["points_per_goal"]),
            mvp_bonus_enabled=bool(values.get("mvp_bonus_enabled", False)),
            clean_sheet_enabled=bool(values.get("clean_sheet_enabled", False)),
            clean_sheet_bonus=float(values["clean_sheet_bonus"]),
            defense_modifier_enabled=bool(values.get("defense_modifier_enabled", True)),
        )


@dataclass
class PlayerProjection:
    """Proiezioni statistiche giocatore"""
    id: int
    nome: str
    ruolo: str
    squadra: str

    # Disponibilità
    p_availability: float  # Probabilità base gioca (0-1)

    # Voto base
    mv_mean: float  # Media voto atteso
    mv_std: float   # Deviazione standard

    # Tassi eventi (per 90 minuti)
    goal_rate: float = 0.0
    assist_rate: float = 0.0
    yellow_rate: float = 0.0
    red_rate: float = 0.0
    own_goal_rate: float = 0.0

    # Solo portieri
    goals_conceded_rate: float = 0.0
    penalties_saved_rate: float = 0.0

    # Flags
    is_penalty_taker: bool = False
    is_set_piece_taker: bool = False


@dataclass
class FixtureDifficulty:
    """Difficoltà fixture per giornata"""
    matchday: int
    opponent: str
    is_home: bool
    opp_attack: float  # 0-10 (per P, D)
    opp_defense: float  # 0-10 (per C, A)


class MonteCarloSimulator:

    def _run_with_log(self, operation, *args, **kwargs):
        """Esegue l'operazione senza creare file di log."""
        return operation(*args, **kwargs)

    """Simulatore Monte Carlo stagione fantacalcio"""

    def __init__(self,
                 settings: LeagueSettings,
                 root_path: Path,
                 league_config: Optional[LeagueConfig] = None,
                 preloaded_team_strength: Optional[Dict[str, Dict[str, float]]] = None,
                 preloaded_calendar_records: Optional[List[Dict[str, Any]]] = None):
        self.settings = settings
        self.root_path = root_path
        self.league_config = league_config or LeagueConfig()
        self.rng = np.random.default_rng()

        # Cache per fixture difficulty (evita ricalcoli ripetuti)
        self._fixture_cache = {}
        self._opponent_strength_cache = {}

        # Carica dati. Nei worker ProcessPool riusiamo i dati statici gia'
        # caricati dal processo principale, evitando letture duplicate da disco.
        if preloaded_team_strength is not None:
            self.team_strength = preloaded_team_strength
        else:
            self.team_strength = self._load_team_strength()

        if preloaded_calendar_records is not None:
            self.calendar = pd.DataFrame(preloaded_calendar_records)
        else:
            self.calendar = self._load_serie_a_calendar()

        # Cache per evitare di ricalcolare dati invarianti milioni di volte.
        # Queste strutture NON cambiano tra una simulazione e l'altra.
        self._projection_cache = {}
        self._fixture_cache = {}
        self._fixture_modifier_cache = {}

        # Cache esclusivamente per dati invarianti delle rose.
        # La scelta della formazione e le estrazioni casuali restano dinamiche.
        self._roster_projection_cache = {}
        self._roster_projection_index_cache = {}

        # Cache del piano pre-match deterministico per rosa/giornata.
        # NON contiene alcun risultato simulato: salva solo la decisione
        # deterministica del LineupService (modulo, titolari, panchina,
        # expected score). Per una stessa rosa e giornata il risultato è
        # identico tra le simulazioni, quindi ricalcolarlo milioni di volte
        # non aggiunge profondità analitica ma solo overhead.
        self._lineup_plan_cache = {}

        # Numero massimo di processi per l'eventuale parallelizzazione.
        # 4 è un default conservativo e adatto alla maggior parte dei PC.
        self.max_workers = min(4, max(1, (os.cpu_count() or 2)))
        self._lineup_adapter = MonteCarloLineupAdapter(settings)

    def _load_team_strength(self) -> Dict[str, Dict[str, float]]:
        """Carica forza squadre Serie A"""
        squadre_path = self.root_path / "data" / "squadre.csv"

        if not squadre_path.exists():
            # Default se non esiste
            print("[Monte Carlo] squadre.csv non trovato, uso valori default")
            return self._get_default_team_strength()

        df = pd.read_csv(squadre_path, delimiter=';')
        strength = {}

        for _, row in df.iterrows():
            strength[row['squadra']] = {
                'attack': float(row.get('rating_att', 5.0)),
                'defense': float(row.get('rating_dif', 5.0)),
                'european_cup': bool(row.get('coppa_europea', 0))
            }

        return strength

    def _get_default_team_strength(self) -> Dict[str, Dict[str, float]]:
        """Valori default forza squadre"""
        default = {'attack': 5.0, 'defense': 5.0, 'european_cup': False}

        # Top teams
        top_teams = {
            'Inter': {'attack': 8.5, 'defense': 8.0, 'european_cup': True},
            'Napoli': {'attack': 8.0, 'defense': 7.5, 'european_cup': True},
            'Milan': {'attack': 7.5, 'defense': 7.0, 'european_cup': True},
            'Juventus': {'attack': 7.5, 'defense': 8.0, 'european_cup': True},
            'Atalanta': {'attack': 8.5, 'defense': 6.5, 'european_cup': True},
            'Roma': {'attack': 7.0, 'defense': 6.5, 'european_cup': True},
            'Lazio': {'attack': 7.0, 'defense': 6.5, 'european_cup': True},
            'Fiorentina': {'attack': 6.5, 'defense': 6.0, 'european_cup': False},
        }

        # Merge con default per squadre mancanti
        all_teams = [
            'Inter', 'Napoli', 'Milan', 'Juventus', 'Atalanta', 'Roma', 'Lazio',
            'Fiorentina', 'Bologna', 'Torino', 'Genoa', 'Empoli', 'Verona',
            'Cagliari', 'Udinese', 'Lecce', 'Parma', 'Como', 'Venezia', 'Monza'
        ]

        result = {}
        for team in all_teams:
            result[team] = top_teams.get(team, default.copy())

        return result

    def _load_serie_a_calendar(self) -> pd.DataFrame:
        """Carica calendario Serie A"""
        calendario_path = self.root_path / "data" / "Calendario" / "calendario_raw.csv"

        print(f"[Monte Carlo] Tentativo caricamento calendario da: {calendario_path}")
        print(f"[Monte Carlo] File esiste? {calendario_path.exists()}")

        if not calendario_path.exists():
            print(f"[Monte Carlo] calendario_raw.csv non trovato in {calendario_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(calendario_path)
            print(f"[Monte Carlo] CSV caricato, righe: {len(df)}, colonne: {list(df.columns)}")

            # Rinomina le colonne per uniformità
            column_mapping = {
                'Wk': 'matchday',
                'Home': 'home_team',
                'Away': 'away_team'
            }

            df = df.rename(columns=column_mapping)
            print(f"[Monte Carlo] Dopo rinomina, colonne: {list(df.columns)}")

            # Verifica che le colonne necessarie esistano
            required_cols = ['matchday', 'home_team', 'away_team']
            if not all(col in df.columns for col in required_cols):
                print(f"[Monte Carlo] Colonne mancanti nel calendario!")
                return pd.DataFrame()

            print(f"[Monte Carlo] [OK] Calendario Serie A caricato: {len(df)} partite")
            return df

        except Exception as e:
            print(f"[Monte Carlo] [ERROR] Errore caricamento calendario: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()


    def _enrich_roster_from_database(
        self,
        roster: List[dict],
        all_players: List[dict]
    ) -> List[dict]:
        """
        Completa la rosa dell'utente con i dati statistici canonici del DB.

        La schermata della rosa può contenere solo anagrafica/quotazione,
        mentre all_players contiene mv_weighted, consistency, gf/ass/amm,
        pv_weighted, status ecc.

        Matching principale: ID giocatore.
        I dati già presenti nella rosa utente hanno priorità; i campi mancanti
        vengono ereditati dal record canonico.

        Se la rosa ha già tutti i dati necessari, salta l'arricchimento.
        """
        # Verifica se la rosa ha già tutti i dati necessari
        required_fields = ['mv_weighted', 'fm_weighted', 'consistency', 'pv_weighted']
        all_complete = True

        for wrapper in roster:
            if not isinstance(wrapper, dict):
                all_complete = False
                break

            player = wrapper.get('player', {})
            if not isinstance(player, dict):
                all_complete = False
                break

            # Controlla se ha tutti i campi richiesti
            for field in required_fields:
                if field not in player or player.get(field) is None:
                    all_complete = False
                    break

            if not all_complete:
                break

        if all_complete:
            print(f"[Projection Merge] Rosa utente già completa, skip arricchimento da DB")
            print(f"[Projection Merge] Rosa utente: {len(roster)}/{len(roster)} giocatori con dati completi")
            return roster

        # Se manca qualcosa, procedi con l'arricchimento
        print(f"[Projection Merge] Rosa incompleta, arricchimento da DB ({len(all_players)} giocatori disponibili)")
        def _norm_id(value):
            if value is None:
                return None
            s = str(value).strip()
            try:
                return str(int(float(s)))
            except (TypeError, ValueError):
                return s.casefold()

        def _norm_name(value):
            if value is None:
                return ""
            s = str(value).strip().casefold()
            # Rimuovi asterisco che indica giocatori nuovi/con dati incompleti
            s = s.replace('*', '').strip()
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            return " ".join(s.split())

        db_by_id = {}
        db_by_name = {}

        for p in all_players:
            if not isinstance(p, dict):
                continue

            pid = p.get('id')
            if pid is not None:
                db_by_id[_norm_id(pid)] = p

            pname = _norm_name(
                p.get('nome', p.get('name', p.get('player_name')))
            )
            if pname:
                db_by_name[pname] = p

        print(f"[Projection Merge] Database: {len(db_by_id)} giocatori per ID, {len(db_by_name)} per nome")

        enriched = []

        for wrapper in roster:
            if not isinstance(wrapper, dict):
                continue

            if isinstance(wrapper.get('player'), dict):
                user_player = dict(wrapper['player'])
                player_id = user_player.get('id')
            else:
                user_player = dict(wrapper)
                player_id = user_player.get('id')

            canonical = db_by_id.get(_norm_id(player_id))

            if canonical is None:
                canonical = db_by_name.get(
                    _norm_name(
                        user_player.get(
                            'nome',
                            user_player.get(
                                'name',
                                user_player.get('player_name')
                            )
                        )
                    )
                )

            if canonical is not None:
                merged = dict(canonical)
                # Dati specifici della rosa utente sovrascrivono solo i
                # campi effettivamente presenti.
                merged.update(user_player)
                enriched.append({'player': merged})
            else:
                enriched.append({'player': user_player})

        matched = 0
        for x in enriched:
            p = x.get('player', {})
            if not isinstance(p, dict):
                continue

            player_id_norm = _norm_id(p.get('id'))
            player_name_norm = _norm_name(
                p.get('nome', p.get('name', p.get('player_name')))
            )

            if player_id_norm in db_by_id:
                matched += 1
            elif player_name_norm in db_by_name:
                matched += 1
            else:
                # DEBUG: giocatore non trovato
                print(f"[Projection Merge] WARNING: Giocatore non matchato - ID: {p.get('id')} (norm: {player_id_norm}), Nome: {p.get('nome')} (norm: {player_name_norm})")

        print(
            f"[Projection Merge] Rosa utente: "
            f"{matched}/{len(enriched)} giocatori collegati ai dati canonici"
        )

        missing_stats = []
        for item in enriched:
            p = item.get('player', {})
            required = ('mv_weighted', 'consistency', 'pv_weighted')
            if not all(k in p and p.get(k) is not None for k in required):
                missing_stats.append(p.get('id'))

        if missing_stats:
            print(
                f"[Projection Merge] WARNING: {len(missing_stats)} giocatori "
                f"ancora senza statistiche complete: {missing_stats[:10]}"
            )
        else:
            print(
                "[Projection Merge] OK: tutti i giocatori della rosa "
                "hanno i campi statistici richiesti."
            )

        return enriched

    def calculate_player_projections(self, player_data: dict) -> PlayerProjection:
        """
        Calcola proiezioni giocatore da dati esistenti.
        Le proiezioni sono immutabili durante una simulazione, quindi vengono
        memorizzate in cache per evitare milioni di ricalcoli.

        Args:
            player_data: dict con campi da database/API
                - id, nome, ruolo, squadra
                - mv_weighted, fm_weighted
                - gf_weighted, ass_weighted, amm_weighted, esp_weighted
                - gs_weighted (portieri), rp_weighted (portieri)
                - pv_weighted (presenze ponderate)
                - status (titolare/ballottaggio/riserva)
                - consistency (deviazione standard voto)
        """
        # Cache per ID giocatore.
        player_id = player_data.get('id')

        try:
            cache_id = str(int(float(player_id)))
        except (TypeError, ValueError):
            cache_id = str(player_id).casefold() if player_id is not None else None

        if cache_id is not None and cache_id in self._projection_cache:
            return self._projection_cache[cache_id]

        # Disponibilità base (status blend)
        p_availability = self._calculate_availability(player_data)

        # FIX BUG #2: USA MV_WEIGHTED, NON FM_WEIGHTED
        # FM include già i bonus storici (gol/assist). Se usiamo FM come base_vote
        # e poi aggiungiamo di nuovo gol/assist simulati, contiamo due volte i bonus.
        # Quindi: base_vote = MV (voto medio pulito), eventi = simulati separatamente.
        mv_mean = player_data.get('mv_weighted', 6.0)
        mv_std = player_data.get('consistency', 0.8)  # Default per ruolo

        # Normalizza numeri eventualmente arrivati come stringhe/NaN.
        try:
            mv_mean = float(mv_mean)
        except (TypeError, ValueError):
            mv_mean = 6.0

        try:
            mv_std = float(mv_std)
        except (TypeError, ValueError):
            mv_std = 0.8

        if not np.isfinite(mv_mean):
            mv_mean = 6.0
        if not np.isfinite(mv_std) or mv_std <= 0:
            mv_std = 0.8

        # Presenze per normalizzare tassi
        pv = max(player_data.get('pv_weighted', 1), 1)

        # Tassi eventi (normalizzati per 90 minuti, scala su 38 giornate)
        goal_rate = player_data.get('gf_weighted', 0.0) / pv
        assist_rate = player_data.get('ass_weighted', 0.0) / pv
        yellow_rate = player_data.get('amm_weighted', 0.0) / pv
        red_rate = player_data.get('esp_weighted', 0.0) / pv
        own_goal_rate = player_data.get('au_weighted', 0.0) / pv

        # Solo portieri
        goals_conceded_rate = 0.0
        penalties_saved_rate = 0.0

        if player_data['ruolo'] == 'P':
            goals_conceded_rate = player_data.get('gs_weighted', 0.0) / pv
            penalties_saved_rate = player_data.get('rp_weighted', 0.0) / pv

        projection = PlayerProjection(
            id=player_data['id'],
            nome=player_data['nome'],
            ruolo=player_data['ruolo'],
            squadra=player_data['squadra'],
            p_availability=p_availability,
            mv_mean=mv_mean,
            mv_std=mv_std,
            goal_rate=goal_rate,
            assist_rate=assist_rate,
            yellow_rate=yellow_rate,
            red_rate=red_rate,
            own_goal_rate=own_goal_rate,
            goals_conceded_rate=goals_conceded_rate,
            penalties_saved_rate=penalties_saved_rate,
            is_penalty_taker=player_data.get('rigorista', False),
            is_set_piece_taker=player_data.get('piazzati', False)
        )

        if cache_id is not None:
            self._projection_cache[cache_id] = projection

        return projection

    def _calculate_availability(self, player_data: dict) -> float:
        """
        Calcola probabilità disponibilità base

        Formula ibrida status + storico (FisherTiger approach):
        - TITOLARE: 85% prior
        - BALLOTTAGGIO: 55% prior
        - RISERVA: 15% prior
        - Blend: 65% status + 35% storico (Pv/38)
        """
        # Storico
        pv = player_data.get('pv_weighted', 0)
        historical_availability = min(pv / 38, 1.0)

        # Status prior
        status = player_data.get('status', 'unknown').lower()
        status_priors = {
            'titolare': 0.85,
            'ballottaggio': 0.55,
            'riserva': 0.15
        }

        if status in status_priors:
            status_prior = status_priors[status]
            # Blend 65-35%
            availability = 0.65 * status_prior + 0.35 * historical_availability
        else:
            # Status mancante/unknown NON significa che il giocatore abbia
            # solo il 15% di probabilità di giocare.
            # Se non abbiamo uno storico utile, usiamo un prior neutro dell'85%.
            if historical_availability <= 0:
                historical_availability = 0.85
            availability = max(historical_availability, 0.85)

        return np.clip(availability, 0.05, 0.95)

    def get_fixture_difficulty(self, team: str, matchday: int) -> FixtureDifficulty:
        """
        Calcola difficoltà fixture per giornata.

        Versione ottimizzata: il calendario viene indicizzato una sola volta
        e poi ogni lookup è O(1), evitando filtri Pandas nel loop Monte Carlo.

        OTTIMIZZAZIONE 2: Cache già implementata (self._fixture_cache)
        """
        """
        Calcola difficoltà fixture per giornata.

        Versione ottimizzata: il calendario viene indicizzato una sola volta
        e poi ogni lookup è O(1), evitando filtri Pandas nel loop Monte Carlo.
        """
        def _norm_team(value):
            if value is None:
                return ""
            s = str(value).strip().casefold()
            s = unicodedata.normalize("NFKD", s)
            s = "".join(ch for ch in s if not unicodedata.combining(ch))
            aliases = {
                "hellas verona": "verona",
                "hellas": "verona",
                "inter milano": "inter",
                "internazionale": "inter",
                "inter": "inter",
                "ac milan": "milan",
                "milan ac": "milan",
                "juve": "juventus",
            }
            s = " ".join(s.split())
            return aliases.get(s, s)

        team_key = _norm_team(team)
        key = (team, int(matchday))

        cached = self._fixture_cache.get(key)
        if cached is not None:
            return cached

        if self.calendar.empty:
            fixture = FixtureDifficulty(
                matchday=matchday,
                opponent='Unknown',
                is_home=True,
                opp_attack=5.0,
                opp_defense=5.0
            )
            self._fixture_cache[key] = fixture
            return fixture

        # Costruisce l'indice al primo utilizzo.
        if not hasattr(self, "_fixture_index"):
            self._fixture_index = {}
            self._fixture_index_normalized = {}

            print(f"[Fixture Index] Costruzione indice da {len(self.calendar)} righe")

            for idx, row in enumerate(self.calendar.itertuples(index=False)):
                row_dict = row._asdict()
                md = row_dict.get("matchday")
                home = row_dict.get("home_team")
                away = row_dict.get("away_team")

                # Debug per le prime 5 righe
                if idx < 5:
                    print(f"[Fixture Index] Riga {idx}: md={md} (type={type(md)}), home={home}, away={away}")

                # Salta righe con dati mancanti
                if pd.isna(md) or pd.isna(home) or pd.isna(away):
                    continue

                try:
                    md = int(float(md))  # Converti float -> int
                except (ValueError, TypeError):
                    continue

                self._fixture_index[(home, md)] = (away, True)
                self._fixture_index[(away, md)] = (home, False)

                self._fixture_index_normalized[(_norm_team(home), md)] = (away, True)
                self._fixture_index_normalized[(_norm_team(away), md)] = (home, False)

            print(f"[Fixture Index] Indice costruito: {len(self._fixture_index)} entries")
            print(f"[Fixture Index] Esempio chiavi: {list(self._fixture_index.keys())[:10]}")

        fixture_data = self._fixture_index.get(key)

        if fixture_data is None:
            fixture_data = self._fixture_index_normalized.get((team_key, int(matchday)))

        if fixture_data is None:
            missing_key = (str(team), int(matchday))
            if not hasattr(self, '_missing_fixture_logged'):
                self._missing_fixture_logged = set()
            if missing_key not in self._missing_fixture_logged:
                self._missing_fixture_logged.add(missing_key)
                print(
                    f"[Fixture WARNING] Nessuna partita trovata per "
                    f"club='{team}' giornata={matchday}"
                )

            fixture = FixtureDifficulty(
                matchday=matchday,
                opponent='Unknown',
                is_home=True,
                opp_attack=5.0,
                opp_defense=5.0
            )
            self._fixture_cache[key] = fixture
            return fixture

        opponent, is_home = fixture_data
        opp_strength = self.team_strength.get(
            opponent,
            {'attack': 5.0, 'defense': 5.0, 'european_cup': False}
        )

        fixture = FixtureDifficulty(
            matchday=matchday,
            opponent=opponent,
            is_home=is_home,
            opp_attack=opp_strength['attack'],
            opp_defense=opp_strength['defense']
        )

        self._fixture_cache[key] = fixture
        return fixture
    def _realistic_event_multiplier(self, player, fixture):
        """
        Riduce la probabilità di combinazioni estreme senza alterare i valori
        medi dei giocatori. L'effetto riguarda gli eventi bonus, non il voto.
        """
        difficulty = 1.0
        try:
            opp_attack = float(getattr(fixture, 'opp_attack', 5.0))
            opp_defense = float(getattr(fixture, 'opp_defense', 5.0))
            difficulty = 0.85 + 0.15 * max(0.0, min(1.0, (10.0 - opp_defense) / 10.0))
            if getattr(fixture, 'is_home', False):
                difficulty *= 1.05
        except Exception:
            pass

        return max(0.70, min(1.10, difficulty))

    def simulate_player_matchday(self,
                                  player: PlayerProjection,
                                  matchday: int) -> Optional[Dict]:
        """
        Simula performance giocatore per una giornata

        Returns:
            None se non disponibile
            Dict con voto, eventi, fantapunteggio se gioca
        """
        # 1. Disponibilità
        fixture = self.get_fixture_difficulty(player.squadra, matchday)

        # Modifica disponibilità per fixture congestion (coppe europee)
        p_available = player.p_availability
        team_info = self.team_strength.get(player.squadra, {'european_cup': False})

        if team_info['european_cup'] and matchday % 3 == 0:
            # Ogni 3 giornate: -7% disponibilità (rotazione)
            p_available *= 0.93

        # Tira disponibilità
        if self.rng.random() > p_available:
            return None  # Non gioca

        # 2. Voto base (Normal distribution)
        base_vote = self.rng.normal(player.mv_mean, player.mv_std)
        base_vote = np.clip(base_vote, 4.0, 9.5)  # Range realistico fantacalcio (non limitare a 8.5)

        # 3. Modificatore fixture difficulty
        vote_modifier = self._calculate_vote_modifier(player, fixture)
        base_vote += vote_modifier
        base_vote = np.clip(base_vote, 4.0, 9.5)

        # 4. Eventi (Poisson distributions)
        events = self._simulate_events(player, fixture)

        # 5. Calcola fantapunteggio
        fantasy_score = self._calculate_fantasy_score(
            player=player,
            base_vote=base_vote,
            events=events,
            fixture=fixture
        )

        return {
            'player_id': player.id,
            'nome': player.nome,
            'ruolo': player.ruolo,
            'matchday': matchday,
            'base_vote': round(base_vote, 1),
            'events': events,
            'fantasy_score': round(fantasy_score, 1),
            'opponent': fixture.opponent,
            'is_home': fixture.is_home
        }

    def _calculate_vote_modifier(self,
                                  player: PlayerProjection,
                                  fixture: FixtureDifficulty) -> float:
        """
        Calcola modificatore voto base da fixture difficulty

        Logica:
        - Casa/trasferta: ±0.1 voto
        - Difficoltà avversario:
            - P, D: difficoltà = attacco avversario
            - C, A: difficoltà = difesa avversario
        - Scaling: avversario forte (8+) -> -0.2, debole (4-) -> +0.2
        """
        cache_key = (
            player.ruolo,
            fixture.opponent,
            fixture.is_home,
            fixture.opp_attack,
            fixture.opp_defense
        )
        cached_modifier = self._fixture_modifier_cache.get(cache_key)
        if cached_modifier is not None:
            return cached_modifier

        modifier = 0.0

        # Casa/trasferta
        if fixture.is_home:
            modifier += 0.1
        else:
            modifier -= 0.05

        # Difficoltà avversario
        if player.ruolo in ['P', 'D']:
            # Difensori: più l'attacco avversario è forte, più difficile
            difficulty = fixture.opp_attack
        else:
            # Attaccanti/centrocampisti: più la difesa avversario è forte, più difficile
            difficulty = fixture.opp_defense

        # Scala difficoltà: 5.0 neutro, 8+ difficile, 3- facile
        difficulty_modifier = (5.0 - difficulty) * 0.08  # ±0.24 max
        modifier += difficulty_modifier

        self._fixture_modifier_cache[cache_key] = modifier
        return modifier

    def _simulate_events(self,
                        player: PlayerProjection,
                        fixture: FixtureDifficulty) -> Dict:
        """
        Simula eventi giocatore (Poisson distributions)

        Returns:
            Dict con conteggi: gol, assist, ammonizioni, espulsioni, autogol, clean_sheet
        """
        # Modifica tassi per fixture difficulty
        goal_rate = player.goal_rate
        assist_rate = player.assist_rate

        if player.ruolo in ['C', 'A']:
            # Attaccanti: più facile segnare contro difese deboli
            difficulty_multiplier = (10 - fixture.opp_defense) / 5.0  # 0.4-2.0
            goal_rate *= difficulty_multiplier
            assist_rate *= difficulty_multiplier

        # Casa/trasferta
        venue_multiplier = 1.15 if fixture.is_home else 0.85
        goal_rate *= venue_multiplier
        assist_rate *= venue_multiplier

        # Tira eventi (Poisson)
        goals = self.rng.poisson(goal_rate) if goal_rate > 0 else 0
        assists = self.rng.poisson(assist_rate) if assist_rate > 0 else 0
        yellows = self.rng.poisson(player.yellow_rate) if player.yellow_rate > 0 else 0
        reds = self.rng.poisson(player.red_rate) if player.red_rate > 0 else 0
        own_goals = self.rng.poisson(player.own_goal_rate) if player.own_goal_rate > 0 else 0

        # Clean sheet per portieri
        clean_sheet = False
        if player.ruolo == 'P' and self.settings.clean_sheet_enabled:
            # Probabilità clean sheet dipende da attacco avversario
            p_clean = max(0.05, (10 - fixture.opp_attack) / 10)
            clean_sheet = self.rng.random() < p_clean

        return {
            'goals': int(goals),
            'assists': int(assists),
            'yellow_cards': min(int(yellows), 1),  # Max 1 per partita
            'red_cards': min(int(reds), 1),  # Max 1 per partita
            'own_goals': int(own_goals),
            'clean_sheet': clean_sheet
        }

    def _calculate_fantasy_score(self,
                                  player: PlayerProjection,
                                  base_vote: float,
                                  events: Dict,
                                  fixture: FixtureDifficulty) -> float:
        """
        Calcola fantapunteggio finale del singolo giocatore

        Formula:
        - Voto base
        - + (gol × goal_bonus)
        - + (assist × assist_bonus)
        - - (ammonizioni × yellow_malus)
        - - (espulsioni × red_malus)
        - - (autogol × own_goal_malus)
        - + (clean_sheet × clean_sheet_bonus) se portiere

        NOTA: Le fasce gol virtuali si applicano SOLO al totale squadra,
        non al singolo giocatore (vedi _calculate_team_score_from_lineup)
        """
        score = base_vote

        # Eventi
        score += events['goals'] * self.settings.goal_bonus
        score += events['assists'] * self.settings.assist_bonus
        score -= events['yellow_cards'] * self.settings.yellow_card_malus
        score -= events['red_cards'] * self.settings.red_card_malus
        score -= events['own_goals'] * self.settings.own_goal_malus

        # Clean sheet portiere
        if events['clean_sheet']:
            score += self.settings.clean_sheet_bonus

        return score

    def simulate_matchday_lineup(self,
                                 rosa: List[dict],
                                 formation: str,
                                 matchday: int,
                                 auto_formation: bool = False,
                                 team_name: str = "TEAM") -> Dict:
        """
        Simula una giornata senza look-ahead bias.

        ORDINE CORRETTO:
        1. Legge calendario/difficoltà.
        2. Stima il rendimento atteso dei giocatori disponibili.
        3. Sceglie modulo e titolari sulla base dell'atteso.
        4. Solo dopo estrae casualmente la prestazione reale dei titolari.

        In questo modo non viene più "scoperto" il voto prima di decidere chi
        schierare.
        """
        roster_cache_key = id(rosa)
        players = self._roster_projection_cache.get(roster_cache_key)
        if players is None:
            if rosa and isinstance(rosa[0], PlayerProjection):
                players = rosa
            else:
                players = []
                for p in rosa:
                    if isinstance(p, PlayerProjection):
                        players.append(p)
                    elif isinstance(p, dict) and p.get('player'):
                        # Rosa utente: dict con chiave 'player'
                        players.append(self.calculate_player_projections(p['player']))
                    elif isinstance(p, dict):
                        # Rose avversarie: dict semplice senza 'player'
                        players.append(self.calculate_player_projections(p))
            self._roster_projection_cache[roster_cache_key] = players

        # L'unica decisione pre-match è il LineupService; da qui in avanti la
        # Monte Carlo si occupa esclusivamente dell'estrazione casuale.
        # Il piano è deterministico per la stessa rosa + giornata + modalità: lo
        # calcoliamo una sola volta e lo riutilizziamo nelle simulazioni successive.
        lineup_cache_key = (
            roster_cache_key,
            int(matchday),
            bool(auto_formation),
            str(formation),
        )
        lineup_plan = self._lineup_plan_cache.get(lineup_cache_key)
        if lineup_plan is None:
            lineup_plan = self._lineup_adapter.recommend(
                rosa, matchday, "auto" if auto_formation else formation
            )
            self._lineup_plan_cache[lineup_cache_key] = lineup_plan
        formation = lineup_plan["formation"]
        selected_ids = {int(player["id"]) for player in lineup_plan["selection"]["starters"]}
        selected_players = {id(player) for player in players if int(player.id) in selected_ids}
        expected_audit = {
            "expected_score": lineup_plan["lineup_summary"]["expected_score"],
            "mean_availability": (
                sum(player["play_probability"] for player in lineup_plan["selection"]["starters"])
                / len(lineup_plan["selection"]["starters"])
                if lineup_plan["selection"]["starters"] else 0.0
            ),
        }

        # Ora, e solo ora, simuliamo le prestazioni reali dei titolari.
        # Manteniamo l'ordine di selezione pre-match per preservare le posizioni.
        starter_order = [
            (int(player["id"]), player.get("role", player.get("ruolo")))
            for player in lineup_plan["selection"]["starters"]
        ]
        if any(role is None for _, role in starter_order):
            raise KeyError("LineupService starter privo sia di 'role' sia di 'ruolo'")
        projected_by_id = self._roster_projection_index_cache.get(roster_cache_key)
        if projected_by_id is None:
            projected_by_id = {int(player.id): player for player in players}
            self._roster_projection_index_cache[roster_cache_key] = projected_by_id

        performances_by_id = {}
        for player_id, role in starter_order:
            if player_id not in projected_by_id:
                continue
            player = projected_by_id[player_id]
            perf = self.simulate_player_matchday(player, matchday)
            if perf:
                performances_by_id[player_id] = perf

        # FIX PROBLEMA #2: Sostituzione rigorosa per ruolo/posizione
        # Se un titolare non gioca, sostituiamo con il primo della panchina dello STESSO RUOLO
        # che effettivamente gioca. Questo preserva la struttura del modulo.
        titolari = []
        for player_id, expected_role in starter_order:
            if player_id in performances_by_id:
                # Titolare disponibile
                titolari.append(performances_by_id[player_id])
            else:
                # Titolare NON disponibile -> cerca sostituto dello stesso ruolo dalla panchina
                for bench_player in lineup_plan["selection"]["bench"]:
                    bench_id = int(bench_player["id"])
                    bench_role = bench_player.get("role", bench_player.get("ruolo"))
                    if bench_role is None:
                        continue

                    if bench_role != expected_role:
                        continue  # Deve essere stesso ruolo
                    if bench_id in performances_by_id:
                        continue  # Già simulato come titolare
                    if bench_id not in projected_by_id:
                        continue  # Non trovato

                    # Simula il sostituto
                    substitute = projected_by_id[bench_id]
                    perf = self.simulate_player_matchday(substitute, matchday)
                    if perf:
                        performances_by_id[bench_id] = perf
                        titolari.append(perf)
                        break  # Trovato sostituto, passa al prossimo slot
                # Se non c'è sostituto dello stesso ruolo disponibile, lo slot resta vuoto
                # -> la squadra gioca con meno di 11 (situazione reale nelle leghe)

        # ============================================================
        # CALCOLO PUNTEGGIO SQUADRA
        # ============================================================
        team_score = self._calculate_team_score_from_lineup(titolari)

        total_score = team_score['total_score']
        virtual_goals = team_score['virtual_goals']

        # Audit compatto: stampa solo una riga per squadra/giornata.
        # Il dettaglio completo si abilita con DEBUG_MC_PLAYERS=1.
        import os
        team_label = team_name or (
            str(getattr(players[0], 'squadra', 'TEAM'))
            if players else 'TEAM'
        )

        if os.getenv("DEBUG_MC_PLAYERS") == "1":
            self._print_simulated_stats(
                team_name=team_label,
                performances=list(performances_by_id.values()),
                matchday=matchday,
                formation=formation,
                total_score=total_score
            )

        print(
            f"[MATCH] {team_label} | MD {matchday} | {formation} | "
            f"atteso={expected_audit['expected_score']:.2f} | "
            f"disp={expected_audit['mean_availability'] * 100:.0f}% | "
            f"simulated={len(performances_by_id)} | titolari={len(titolari)}/11 | "
            f"score={total_score:.2f}"
        )


        return {
            'titolari': titolari,
            'panchina': [],  # FIX: non usiamo più lineup['panchina']
            'player_score': round(team_score['player_score'], 2),
            'defense_modifier': round(team_score['defense_modifier'], 2),
            'mvp_bonus': round(team_score['mvp_bonus'], 2),
            'total_score': round(total_score, 2),
            'virtual_goals': int(virtual_goals),
            'expected_score': round(expected_audit['expected_score'], 2),
            'mean_availability': round(expected_audit['mean_availability'], 4),
            'matchday': matchday,
            'formation_used': formation
        }

    # ============================================================================
    # DEPRECATED LEGACY FUNCTIONS - DO NOT USE
    # ============================================================================
    # Queste funzioni erano parte del vecchio motore di selezione lineup.
    # Ora usiamo MonteCarloLineupAdapter che delega a LineupService.
    # Le funzioni sono mantenute solo per compatibilità temporanea ma NON devono
    # essere richiamate nel flusso principale - causerebbero look-ahead bias.
    # ============================================================================

    def _select_best_lineup(self,
                           performances: List[Dict],
                           formation: str) -> Dict:
        """
        ⚠️ DEPRECATED - DO NOT USE ⚠️
        Questa funzione causa look-ahead bias: riordina i giocatori in base al
        fantasy_score realizzato DOPO la simulazione.

        Usa invece la logica in simulate_matchday_lineup() che preserva l'ordine
        di selezione pre-match determinato da LineupService.
        """
        raise RuntimeError(
            "DEPRECATED: _select_best_lineup() non deve essere usato. "
            "Causa look-ahead bias. Usa simulate_matchday_lineup() invece."
        )

    def _calculate_defense_modifier(self, titolari: List[Dict]) -> float:
        """
        Calcola modificatore difesa (mantra classico)

        Formula:
        - Media voti difensori (solo D)
        - Se >= 6.5: +1 punto
        - Se < 6.0: -1 punto
        """
        defenders = [p for p in titolari if p['ruolo'] == 'D']

        if not defenders:
            return 0.0

        avg_vote = sum(p['base_vote'] for p in defenders) / len(defenders)

        if avg_vote >= 6.5:
            return 1.0
        elif avg_vote < 6.0:
            return -1.0
        else:
            return 0.0

    def _select_optimal_formation(self, performances: List[Dict]) -> str:
        """
        ⚠️ DEPRECATED - DO NOT USE ⚠️
        Questa funzione seleziona il modulo in base ai voti realizzati,
        causando look-ahead bias.

        Usa invece MonteCarloLineupAdapter che delega a LineupService per
        la selezione pre-match del modulo.
        """
        raise RuntimeError(
            "DEPRECATED: _select_optimal_formation() non deve essere usato. "
            "Causa look-ahead bias. Usa MonteCarloLineupAdapter invece."
        )


    def simulate_season(
        self,
        rosa: List[dict],
        formation: str,
        league_calendar: dict,
        my_team: str,
        all_players: List[dict],
        n_simulations: int = 10000,
        progress_callback=None,
        all_players_complete: List[dict] = None
    ) -> Dict:
        """API pubblica con salvataggio automatico del log."""
        # Se non viene passato all_players_complete, usa all_players (backward compatibility)
        if all_players_complete is None:
            all_players_complete = all_players

        return self._run_with_log(
            self._simulate_season_impl,
            rosa=rosa,
            formation=formation,
            league_calendar=league_calendar,
            my_team=my_team,
            all_players=all_players,
            n_simulations=n_simulations,
            progress_callback=progress_callback,
            all_players_complete=all_players_complete
        )

    def _simulate_season_impl(self,
                       rosa: List[dict],
                       formation: str,
                       league_calendar: dict,
                       my_team: str,
                       all_players: List[dict],
                       n_simulations: int = 10000,
                       progress_callback=None,
                       all_players_complete: List[dict] = None) -> Dict:
        """
        Simula intera stagione con Monte Carlo - 3 scenari con rose avversarie diverse

        Args:
            rosa: Rosa giocatori utente (da CompletaRosa)
            formation: Formazione (es. "3-4-3")
            league_calendar: Calendario lega fantacalcio
            my_team: Nome squadra utente nel calendario
            all_players: Lista giocatori disponibili per generare avversari (senza giocatori rosa utente)
            n_simulations: Numero simulazioni per scenario (default 1000)
            all_players_complete: Lista completa giocatori (con giocatori rosa utente, per arricchimento)

        Returns:
            Dict con:
            - scenarios: List[dict] risultato per scenario (3 totali)
            - aggregate_statistics: Dict statistiche aggregate su tutti gli scenari
        """
        print(f"[Monte Carlo] Avvio 3 scenari con {n_simulations} simulazioni ciascuno...")

        # Se non viene passato all_players_complete, usa all_players (backward compatibility)
        if all_players_complete is None:
            all_players_complete = all_players

        # Converti rosa utente in player_ids
        my_player_ids = [p['player']['id'] for p in rosa if p.get('player')]

        # IMPORTANTE:
        # La rosa proveniente dalla UI può non contenere tutte le statistiche
        # necessarie al motore. Usiamo all_players_complete (database completo)
        # per completare i campi mancanti per ogni ID.
        rosa_enriched = self._enrich_roster_from_database(
            rosa,
            all_players_complete  # ← Usa database COMPLETO (include giocatori rosa utente)
        )

        # Ottieni lista squadre lega
        opponent_teams = [t for t in league_calendar['teams'] if t != my_team]

        scenarios_results = []
        previous_opponent_rosters = None

        # ==========================================
        # OTTIMIZZAZIONE 1: PARALLELIZZAZIONE
        # Esegui i 3 scenari in parallelo usando ThreadPoolExecutor
        # (Thread invece di Process perché condividono memoria cache)
        # ==========================================

        print(f"[Monte Carlo] Avvio 3 scenari IN PARALLELO con {n_simulations} simulazioni ciascuno...")

        # Prepara i 3 scenari con rose diverse
        scenario_configs = []
        for scenario_idx in range(3):
            scenario_id = scenario_idx + 1
            print(f"\n[Scenario {scenario_id}/3] Generazione rose avversarie...")

            opponent_rosters = self._generate_opponent_rosters(
                all_players=all_players,
                my_player_ids=my_player_ids,
                opponent_teams=opponent_teams,
                previous_rosters=previous_opponent_rosters,
                scenario_id=scenario_id
            )

            # Diagnostica completa delle rose avversarie
            for _team_name, _roster in opponent_rosters.items():
                self._print_roster_diagnostics(
                    _team_name,
                    _roster,
                    is_user=False,
                    scenario_id=scenario_id
                )

            # Verifica differenza rose
            if previous_opponent_rosters is not None:
                print(f"  [Scenario {scenario_id}] Verifica differenza rose:")
                for team in opponent_teams:
                    prev_ids = {p['id'] for p in previous_opponent_rosters.get(team, [])}
                    curr_ids = {p['id'] for p in opponent_rosters.get(team, [])}
                    different = len(curr_ids - prev_ids)
                    print(
                        f"    {team}: {different}/25 diversi "
                        f"({'OK' if different >= 13 else 'ERRORE'})"
                    )

            previous_opponent_rosters = {
                team: list(roster) for team, roster in opponent_rosters.items()
            }

            self._print_team_strength_audit(
                my_team,
                rosa_enriched,
                opponent_rosters,
                scenario_idx + 1
            )

            # Salva configurazione scenario
            scenario_configs.append({
                'scenario_id': scenario_id,
                'my_team': my_team,
                'my_roster': rosa_enriched,
                'opponent_rosters': opponent_rosters,
                'draft_audit': getattr(self, '_last_draft_audit', {}),
                'formation': formation,
                'league_calendar': league_calendar,
                'n_simulations': n_simulations,
                'settings_dict': asdict(self.settings),  # Serializza LeagueSettings
                'league_config_dict': {
                    'starting_budget': self.league_config.starting_budget,
                    'participants': self.league_config.participants,
                    'min_price': self.league_config.min_price,
                    'bid_increment': self.league_config.bid_increment,
                    'reserve': self.league_config.reserve,
                    'scoring': self.league_config.scoring,
                    'formations': self.league_config.formations,
                    'roster_composition': self.league_config.roster_composition,
                },
                'root_path': str(self.root_path),  # Serializza Path
                # Dati statici gia' caricati nel processo principale: vengono
                # passati ai worker per evitare letture duplicate dei CSV.
                'preloaded_team_strength': self.team_strength,
                'preloaded_calendar_records': self.calendar.to_dict(orient='records') if not self.calendar.empty else [],
            })

        # ==========================================
        # PARALLELIZZAZIONE CON ProcessPoolExecutor
        # I 3 scenari girano in 3 processi separati = 3 core CPU indipendenti
        # Usa Manager.Queue per comunicazione progress inter-processo
        # ==========================================
        print(f"\n[PARALLELIZZAZIONE ProcessPool] Esecuzione 3 scenari su 3 processi...")

        # Crea Manager.Queue per comunicazione inter-processo
        manager = Manager()
        progress_queue = manager.Queue()

        # Aggiungi progress_queue a ogni config
        for config in scenario_configs:
            config['progress_queue'] = progress_queue

        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = []
            for config in scenario_configs:
                future = executor.submit(_run_scenario_in_process, config)
                futures.append(future)

            # Raccogli risultati mentre leggi progress dalla queue
            for idx, future in enumerate(futures):
                print(f"[Main] Attendendo risultato scenario {idx + 1}/3...")

                # Leggi progress dalla queue mentre aspetti
                while not future.done():
                    try:
                        progress_data = progress_queue.get(timeout=0.1)
                        # Chiama il callback con i dati ricevuti
                        if progress_callback:
                            progress_callback(
                                progress_data['scenario_id'],
                                progress_data['completed'],
                                progress_data['total'],
                                progress_data['progress']
                            )
                    except:
                        pass  # Timeout o queue vuota

                result = future.result()
                scenarios_results.append(result)
                print(f"[Main] Scenario {idx + 1}/3 ricevuto!")

        print(f"\n[Monte Carlo] Tutti gli scenari completati, avvio aggregazione...")

        # Aggrega statistiche su tutti gli scenari (3000 simulazioni totali)
        aggregate_stats = self._aggregate_scenarios(scenarios_results, my_team)

        # Identifica MIGLIORE e PEGGIOR risultato possibile attraverso TUTTI gli scenari
        # Non "scenario migliore", ma "migliore risultato mai ottenuto"
        all_positions = []
        all_points = []
        for scenario in scenarios_results:
            all_positions.extend(scenario.get('my_team_positions_raw', []))
            all_points.extend(scenario.get('my_team_points_raw', []))

        # Trova la simulazione con la MIGLIORE posizione finale
        best_position_idx = all_positions.index(min(all_positions))
        best_result = {
            'final_position': min(all_positions),
            'total_points': all_points[best_position_idx] if best_position_idx < len(all_points) else None,
            'type': 'best'
        }

        # Trova la simulazione con la PEGGIORE posizione finale
        worst_position_idx = all_positions.index(max(all_positions))
        worst_result = {
            'final_position': max(all_positions),
            'total_points': all_points[worst_position_idx] if worst_position_idx < len(all_points) else None,
            'type': 'worst'
        }

        print(f"\n[Monte Carlo] Completato! 3 scenari × {n_simulations} = {3 * n_simulations} simulazioni totali")

        # Stampa riepilogo migliore e peggior risultato possibile
        self._print_result_box(best_result, aggregate_stats, my_team, 'best', len(all_positions))
        self._print_result_box(worst_result, aggregate_stats, my_team, 'worst', len(all_positions))

        return _json_safe({
            'scenarios': scenarios_results,
            'aggregate_statistics': aggregate_stats,
            'best_result': best_result,
            'worst_result': worst_result,
            'my_team': my_team,
            'total_simulations': 3 * n_simulations
        })

    def _print_roster_diagnostics(
        self,
        team_name: str,
        roster: List[dict],
        is_user: bool = False,
        scenario_id: Optional[int] = None
    ):
        """
        Stampa la rosa completa e le statistiche attese dei giocatori.
        Le statistiche simulate vengono stampate separatamente quando
        disponibili durante una giornata/simulazione.
        """
        label = "TUA ROSA" if is_user else f"AVVERSARIO {team_name}"
        scenario_label = f" | SCENARIO {scenario_id}" if scenario_id else ""

        print("\n" + "=" * 100)
        print(f"[ROSTER DEBUG] {label}{scenario_label}")
        print("=" * 100)

        rows = []
        for p in roster:
            if isinstance(p, PlayerProjection):
                player = p
                raw = {}
            else:
                raw = p.get('player', p) if isinstance(p, dict) else {}
                player = self.calculate_player_projections(raw)

            rows.append({
                'id': player.id,
                'nome': getattr(player, 'nome', raw.get('nome', '?')),
                'ruolo': player.ruolo,
                'squadra': player.squadra,
                'fm': float(raw.get('fm_weighted', raw.get('overall', 0)) or 0),
                'mv_mean': float(player.mv_mean),
                'mv_std': float(player.mv_std),
                'availability': float(player.p_availability),
                'goal_rate': float(player.goal_rate),
                'assist_rate': float(player.assist_rate),
                'yellow_rate': float(player.yellow_rate),
                'red_rate': float(player.red_rate),
                'bonus_rate': float(
                    player.goal_rate + player.assist_rate
                ),
            })

        role_order = {'P': 0, 'D': 1, 'C': 2, 'A': 3}
        rows.sort(key=lambda x: (role_order.get(x['ruolo'], 9), -x['fm']))

        print(
            f"{'RUOLO':<6}{'GIOCATORE':<25}{'TEAM':<18}"
            f"{'FM':>7}{'MV':>7}{'SD':>7}{'DISP':>8}"
            f"{'GOL':>8}{'AST':>8}{'GIAL':>8}{'ROSS':>8}"
        )
        print("-" * 100)

        for r in rows:
            print(
                f"{r['ruolo']:<6}"
                f"{str(r['nome'])[:24]:<25}"
                f"{str(r['squadra'])[:17]:<18}"
                f"{r['fm']:>7.2f}"
                f"{r['mv_mean']:>7.2f}"
                f"{r['mv_std']:>7.2f}"
                f"{r['availability'] * 100:>7.1f}%"
                f"{r['goal_rate']:>8.3f}"
                f"{r['assist_rate']:>8.3f}"
                f"{r['yellow_rate']:>8.3f}"
                f"{r['red_rate']:>8.3f}"
            )

        if rows:
            top11 = sorted(rows, key=lambda x: x['fm'], reverse=True)[:11]
            print("-" * 100)
            print(
                f"[ROSTER SUMMARY] {team_name}: "
                f"FM medio={sum(x['fm'] for x in rows)/len(rows):.2f} | "
                f"MV medio={sum(x['mv_mean'] for x in rows)/len(rows):.2f} | "
                f"Top11 FM medio={sum(x['fm'] for x in top11)/11:.2f}"
            )

    def _print_simulated_stats(
        self,
        team_name: str,
        performances: List[dict],
        matchday: int,
        formation: str,
        total_score: float
    ):
        """Stampa le statistiche effettivamente simulate per i titolari."""
        print("\n" + "-" * 100)
        print(
            f"[SIMULATED] {team_name} | Giornata {matchday} | "
            f"Modulo {formation} | Punteggio={total_score:.2f}"
        )
        print(
            f"{'GIOCATORE':<25}{'VOTO':>7}{'G+':>6}{'AST':>6}"
            f"{'GIAL':>7}{'ROSS':>7}{'BONUS':>8}{'FM SCORE':>10}"
        )
        print("-" * 100)

        for p in sorted(
            performances,
            key=lambda x: float(x.get('fantasy_score', 0)),
            reverse=True
        ):
            print(
                f"{str(p.get('nome', p.get('name', p.get('player_name', '?'))))[:24]:<25}"
                f"{float(p.get('base_vote', 0)):>7.2f}"
                f"{float(p.get('events', {}).get('goals', 0)):>6.0f}"
                f"{float(p.get('events', {}).get('assists', 0)):>6.0f}"
                f"{float(p.get('events', {}).get('yellow_cards', 0)):>7.0f}"
                f"{float(p.get('events', {}).get('red_cards', 0)):>7.0f}"
                f"{float(p.get('fantasy_score', 0) - p.get('base_vote', 0)):>8.2f}"
                f"{float(p.get('fantasy_score', 0)):>10.2f}"
            )

    def _generate_opponent_rosters(self,
                                   all_players: List[dict],
                                   my_player_ids: List[int],
                                   opponent_teams: List[str],
                                   variation_from_previous: float = 0.0,
                                   previous_rosters: Optional[Dict[str, List[dict]]] = None,
                                   scenario_id: int = 1) -> Dict[str, List[dict]]:
        """
        Genera rose avversarie realistiche, differenziate e con forza controllata.

        Regole:
        1) Ogni rosa ha 25 giocatori: 3 P, 8 D, 8 C, 6 A.
        2) All'interno di uno scenario non vengono duplicati giocatori tra squadre
           finché il database ha abbastanza elementi.
        3) Scenario 1/2/3 hanno distribuzioni di forza diverse.
        4) Per scenario 2 e 3 ogni squadra deve avere almeno il 50% di giocatori
           diversi rispetto allo scenario precedente: 13/25.
        5) La forza viene valutata soprattutto sulla qualità della rosa utilizzabile,
           non solo sulla media dei 25 giocatori.
        """
        available = [player for player in all_players if player.get('id') not in my_player_ids]
        draft = BudgetAwareSnakeDraft(self.league_config, self.rng, allow_budget_overflow=True)
        rosters = draft.draft(available, opponent_teams)
        self._last_draft_audit = draft.last_audit
        for team, roster in rosters.items():
            spent = sum(float(player['simulated_price']) for player in roster)
            remaining = self.league_config.starting_budget - spent
            if len(roster) != sum(self.league_config.roster_composition.values()) or remaining < self.league_config.reserve - 1e-9:
                raise RuntimeError(f"Rosa avversaria non completabile per {team}")
            audit = draft.last_audit[team]
            print(
                f"  [Snake Draft] {team}: {len(roster)} giocatori, "
                f"AV {audit['theoretical_value']:.0f}, spesi {spent:.0f}/{self.league_config.starting_budget:.0f}, "
                f"surplus {audit['surplus']:.0f}, efficienza {audit['efficiency']:.3f}, residuo {remaining:.0f}"
            )
        return rosters

    def _project_roster(self, roster: List[dict]) -> List[PlayerProjection]:
        """Pre-calcola le proiezioni della rosa una sola volta.

        Accetta sia:
        - {'player': {...}} usato dalla rosa utente
        - {...} player dict grezzo usato dalle rose avversarie
        - PlayerProjection già proiettati
        """
        projected = []
        for p in roster:
            if isinstance(p, PlayerProjection):
                projected.append(p)
                continue

            if not isinstance(p, dict):
                continue

            # Rosa utente: wrapper {'player': {...}}
            if isinstance(p.get('player'), dict):
                player_data = p['player']
            # Rose avversarie: player dict direttamente
            elif p.get('id') is not None and p.get('nome') is not None:
                player_data = p
            else:
                continue

            projected.append(self.calculate_player_projections(player_data))

        return projected


    def _calculate_team_score_from_lineup(self, titolari: List[Dict]) -> Dict:
        """
        Calcola il punteggio complessivo della squadra dagli 11 titolari.

        FIX: defense_modifier e mvp_bonus DEVONO essere calcolati sui voti SIMULATI,
        non azzerati. La differenza tra expected e actual è:
        - Expected: modifier calcolato su voti attesi (LineupService)
        - Actual: modifier calcolato su voti simulati (qui)

        Questo è CORRETTO perché le regole della lega si applicano al risultato reale.

        IMPORTANTE:
        - la soglia dei gol virtuali viene applicata SOLO al totale squadra;
        - la disponibilità non viene moltiplicata per il punteggio;
        - il metodo è usato anche per l'audit, così il passaggio
          giocatori -> squadra -> gol è completamente trasparente.
        """
        player_score = sum(
            float(p.get('fantasy_score', 0.0))
            for p in titolari
        )

        defense_modifier = 0.0
        if getattr(self.settings, 'defense_modifier_enabled', False):
            try:
                defense_modifier = float(
                    self._calculate_defense_modifier(titolari)
                )
            except Exception:
                defense_modifier = 0.0

        mvp_bonus = 0.0
        if getattr(self.settings, 'mvp_bonus_enabled', False) and titolari:
            # L'MVP viene determinato sul voto base SIMULATO
            mvp = max(
                titolari,
                key=lambda p: float(p.get('base_vote', 0.0))
            )
            mvp_bonus = 1.0 if mvp else 0.0

        total_score = player_score + defense_modifier + mvp_bonus
        virtual_goals = self._calculate_virtual_goals(total_score)

        return {
            'player_score': float(player_score),
            'defense_modifier': float(defense_modifier),
            'mvp_bonus': float(mvp_bonus),
            'total_score': float(total_score),
            'virtual_goals': int(virtual_goals),
        }

    def _print_team_strength_audit(
        self,
        my_team: str,
        my_roster: List[dict],
        opponent_rosters: Dict[str, List[dict]],
        scenario_id: int
    ):
        """Confronto sintetico della forza delle rose, senza modificare il modello."""

        def unwrap(raw):
            if isinstance(raw, dict) and isinstance(raw.get('player'), dict):
                return raw['player']
            return raw

        def value(raw):
            p = unwrap(raw)
            # Usa solo fm_weighted per il calcolo della forza
            # overall può contenere valori 0-100 che distorcono il calcolo
            for key in ('fm_weighted', 'mv_weighted'):
                try:
                    val = p.get(key)
                    if val is not None and float(val) > 0:
                        return float(val)
                except Exception:
                    pass
            return 6.0  # Default realistico per giocatori senza dati

        teams = [(my_team, my_roster, True)]
        teams.extend(
            (team, roster, False)
            for team, roster in opponent_rosters.items()
        )

        print()
        print("=" * 100)
        print(f"[TEAM STRENGTH AUDIT] SCENARIO {scenario_id}")
        print("=" * 100)
        print(
            f"{'SQUADRA':<25}"
            f"{'N':>4}"
            f"{'FM MEDIA':>10}"
            f"{'TOP11':>10}"
            f"{'FORZA':>10}"
        )
        print("-" * 100)

        for team, roster, is_user in teams:
            vals = sorted(
                [value(p) for p in roster],
                reverse=True
            )
            mean = sum(vals) / len(vals) if vals else 0.0
            top11 = (
                sum(vals[:11]) / min(11, len(vals))
                if vals else 0.0
            )
            strength = 0.70 * top11 + 0.30 * mean

            prefix = "*" if is_user else " "
            print(
                f"{prefix}{team:<24}"
                f"{len(vals):>4}"
                f"{mean:>10.2f}"
                f"{top11:>10.2f}"
                f"{strength:>10.2f}"
            )

        print("=" * 100)
        print("* = tua squadra")

    def _print_matchday_audit(
        self,
        scenario_id: int,
        simulation_id: int,
        matchday_num: int,
        all_teams: List[str],
        matchday_results: Dict[str, Dict],
        matchday_scores: Dict[str, float]
    ):
        """Audit delle prime 3 giornate della prima simulazione di scenario."""

        print()
        print(
            f"[MATCH AUDIT] S{scenario_id} "
            f"| SIM {simulation_id} "
            f"| GIORNATA {matchday_num}"
        )
        print("-" * 100)

        for team in all_teams:
            result = matchday_results.get(team)
            if not result:
                continue

            titolari = result.get('titolari', [])
            player_score = sum(
                float(p.get('fantasy_score', 0.0))
                for p in titolari
            )

            total_score = float(
                result.get('total_score', matchday_scores.get(team, 0.0))
            )

            virtual_goals = int(
                result.get(
                    'virtual_goals',
                    self._calculate_virtual_goals(total_score)
                )
            )

            avg_vote = (
                sum(float(p.get('base_vote', 0.0)) for p in titolari)
                / len(titolari)
                if titolari else 0.0
            )

            available = sum(
                1 for p in titolari
                if p.get('played', True)
            )

            print(
                f"{team:<25}"
                f"XI={len(titolari):>2}/11 "
                f"giocano={available:>2}/11 "
                f"voto={avg_vote:>5.2f} "
                f"player={player_score:>6.2f} "
                f"totale={total_score:>6.2f} "
                f"gol={virtual_goals}"
            )

        print("-" * 100)

    def _simulate_season_scenario(self,
                                  my_team: str,
                                  my_roster: List[dict],
                                  opponent_rosters: Dict[str, List[dict]],
                                  formation: str,
                                  league_calendar: dict,
                                  n_simulations: int,
                                  scenario_id: int,
                                  progress_callback=None) -> Dict:
        """
        Simula stagione completa per un singolo scenario

        Returns:
            Dict con statistiche posizioni, punti, ecc.
        """
        all_teams = [my_team] + list(opponent_rosters.keys())
        n_teams = len(all_teams)

        # Tracciamento risultati
        final_positions = {team: [] for team in all_teams}  # Posizione finale per simulazione
        final_points = {team: [] for team in all_teams}

        print(f"  [Scenario {scenario_id}] Inizio simulazione: {n_simulations} iterazioni per {n_teams} squadre")

        # Inizializza file di log per questo scenario
        from pathlib import Path
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "simulation_debug.log"

        if scenario_id == 1:
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("=== SIMULATION DEBUG LOG ===\n")
                    f.write(f"Timestamp: {__import__('datetime').datetime.now()}\n")
                    f.write(f"Log file: {log_file}\n\n")
            except Exception as e:
                print(f"[Warning] Impossibile creare log file: {e}")

        for sim_idx in range(n_simulations):
            try:
                # Progress callback OGNI simulazione
                if progress_callback:
                    progress = ((sim_idx + 1) / n_simulations) * 100
                    progress_callback(scenario_id, sim_idx + 1, n_simulations, progress)

                # Stampa progresso ogni 10 simulazioni
                if (sim_idx + 1) % 10 == 0:
                    print(f"  [Scenario {scenario_id}] Simulazione {sim_idx + 1}/{n_simulations} completata", flush=True)

                # Reset classifica
                points = {team: 0 for team in all_teams}
                goals_for = {team: 0 for team in all_teams}
                goals_against = {team: 0 for team in all_teams}
                total_scores = {team: 0.0 for team in all_teams}

                # Log inizio simulazione
                if (sim_idx + 1) % 50 == 1 or sim_idx == 0:
                    print(f"    [Sim {sim_idx + 1}] Avvio stagione completa (34 giornate)...", flush=True)

                # Simula ogni giornata
                for matchday_data in league_calendar['matchdays']:
                    matchday_num = matchday_data['matchday']

                    # Log configurazione per prime simulazioni
                    if sim_idx == 0 and matchday_num == 1:
                        from pathlib import Path
                        log_file = Path(__file__).parent.parent.parent / "logs" / "simulation_debug.log"
                        log_msg = f"    [Config] goal_threshold={self.settings.goal_threshold}, points_per_goal={self.settings.points_per_goal}"
                        print(log_msg, flush=True)
                        # Salva anche su file
                        try:
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"\n=== Scenario {scenario_id} ===\n")
                                f.write(log_msg + "\n")
                        except Exception as e:
                            print(f"[Warning] Errore scrittura log: {e}")

                    # Calcola punteggi per tutte le squadre
                    matchday_scores = {}
                    matchday_results = {}

                    # Squadra utente (sceglie automaticamente il miglior modulo ogni giornata)
                    lineup_result = self.simulate_matchday_lineup(
                        my_roster,
                        formation,
                        matchday_num,
                        auto_formation=True,
                        team_name=my_team
                    )
                    matchday_scores[my_team] = lineup_result['total_score']
                    matchday_results[my_team] = lineup_result
                    total_scores[my_team] += lineup_result['total_score']

                    # Squadre avversarie (anche loro scelgono automaticamente)
                    for opp_team, opp_roster in opponent_rosters.items():
                        opp_result = self.simulate_matchday_lineup(
                            opp_roster,
                            formation,
                            matchday_num,
                            auto_formation=True,
                            team_name=opp_team
                        )
                        matchday_scores[opp_team] = opp_result['total_score']
                        matchday_results[opp_team] = opp_result
                        total_scores[opp_team] += opp_result['total_score']

                    # Processa fixture della giornata
                    for fixture in matchday_data['fixtures']:
                        home = fixture['home']
                        away = fixture['away']

                        home_score = matchday_scores.get(home, 0)
                        away_score = matchday_scores.get(away, 0)

                        # Calcola gol virtuali
                        home_goals = int(
                            matchday_results.get(home, {}).get(
                                'virtual_goals',
                                self._calculate_virtual_goals(home_score)
                            )
                        )
                        away_goals = int(
                            matchday_results.get(away, {}).get(
                                'virtual_goals',
                                self._calculate_virtual_goals(away_score)
                            )
                        )

                        # Log dettagliato per prime 3 simulazioni e prime 5 giornate
                        if sim_idx < 3 and matchday_num <= 5:
                            from pathlib import Path
                            log_file = Path(__file__).parent.parent.parent / "logs" / "simulation_debug.log"
                            log_msg = f"      [{matchday_num}] {home} vs {away}: Pt {home_score:.1f}-{away_score:.1f} -> Gol {home_goals}-{away_goals}"
                            print(log_msg, flush=True)
                            # Salva anche su file
                            try:
                                with open(log_file, "a", encoding="utf-8") as f:
                                    f.write(log_msg + "\n")
                            except Exception:
                                pass

                        goals_for[home] += home_goals
                        goals_against[home] += away_goals
                        goals_for[away] += away_goals
                        goals_against[away] += home_goals

                        # Assegna punti classifica
                        if home_goals > away_goals:
                            points[home] += 3
                        elif away_goals > home_goals:
                            points[away] += 3
                        else:
                            points[home] += 1
                            points[away] += 1

                # Audit diagnostico: solo prima simulazione e prime 3 giornate.
                if sim_idx == 0 and matchday_num <= 3:
                    self._print_matchday_audit(
                        scenario_id,
                        sim_idx + 1,
                        matchday_num,
                        all_teams,
                        matchday_results,
                        matchday_scores
                    )

                # Calcola classifica finale con tiebreakers
                standings = self._calculate_standings(
                    teams=all_teams,
                    points=points,
                    goals_for=goals_for,
                    goals_against=goals_against,
                    total_scores=total_scores
                )

                # Log classifica per prime 3 simulazioni
                if sim_idx < 3:
                    print(f"    [Sim {sim_idx + 1}] Classifica finale:", flush=True)
                    for pos, team in enumerate(standings[:5], start=1):
                        marker = "*" if team == my_team else " "
                        print(f"      {pos}. {marker}{team}: {points[team]} punti", flush=True)

                # Registra posizioni
                for position, team in enumerate(standings, start=1):
                    final_positions[team].append(position)
                    final_points[team].append(points[team])

            except Exception as e:
                print(f"\n  [Scenario {scenario_id}] ERRORE simulazione {sim_idx + 1}/{n_simulations}:")
                print(f"  [ERROR] Tipo: {type(e).__name__}")
                print(f"  [ERROR] Messaggio: {str(e)}")
                import traceback
                print(f"  [ERROR] Traceback:")
                traceback.print_exc()
                # Continua con la prossima simulazione invece di bloccarsi
                continue

        print(f"\r  [Scenario {scenario_id}] Simulazione completata ({n_simulations}/{n_simulations})    ")

        # Verifica che abbiamo risultati
        successful_sims = sum(len(positions) for positions in final_positions.values())
        if successful_sims == 0:
            error_msg = f"Scenario {scenario_id}: Nessun risultato generato! Tutte le {n_simulations} simulazioni sono fallite."
            print(f"\n  [ERROR] {error_msg}")
            print(f"  [DEBUG] Controlla gli errori stampati sopra per il dettaglio.")
            raise Exception(error_msg)
        elif successful_sims < n_simulations * len(all_teams):
            failed = n_simulations - (successful_sims // len(all_teams))
            print(f"  [WARNING] {failed}/{n_simulations} simulazioni fallite, ma continuiamo con i dati disponibili")

        # Calcola statistiche
        statistics = {}
        for team in all_teams:
            positions = final_positions[team]
            pts = final_points[team]

            # Distribuzione posizioni
            position_dist = {}
            position_counts = np.bincount(
                np.asarray(positions, dtype=np.int16),
                minlength=n_teams + 1
            )
            for pos in range(1, n_teams + 1):
                position_dist[int(pos)] = float(
                    position_counts[pos] / n_simulations * 100
                )

            statistics[team] = {
                'mean_position': np.mean(positions),
                'median_position': np.median(positions),
                'position_distribution': position_dist,
                'mean_points': np.mean(pts),
                'median_points': np.median(pts),
                'std_points': np.std(pts),
                'probability_win': position_dist.get(1, 0),
                'probability_top3': sum(position_dist.get(i, 0) for i in range(1, 4)),
                'probability_top6': sum(position_dist.get(i, 0) for i in range(1, 7))
            }

        return {
            'scenario_id': scenario_id,
            'n_simulations': n_simulations,
            'statistics': statistics,
            # Conserviamo i punti reali della squadra utente per aggregazioni
            # future senza dover ricostruire una normale artificiale.
            'my_team_points_raw': [float(x) for x in final_points.get(my_team, [])],
            'my_team_positions_raw': [int(x) for x in final_positions.get(my_team, [])]
        }

    def _calculate_virtual_goals(self, score: float) -> int:
        """Calcola gol virtuali da punteggio fantacalcio"""
        if score < self.settings.goal_threshold:
            return 0
        return 1 + int((score - self.settings.goal_threshold) / self.settings.points_per_goal)

    def _calculate_standings(self,
                            teams: List[str],
                            points: Dict[str, int],
                            goals_for: Dict[str, int],
                            goals_against: Dict[str, int],
                            total_scores: Dict[str, float]) -> List[str]:
        """
        Calcola classifica finale con tiebreakers

        Ordine:
        1. Punti
        2. Differenza reti
        3. Reti fatte
        4. Punteggio fantacalcio totale stagione
        """
        def sort_key(team: str):
            return (
                -points[team],  # Più punti = meglio (negativo per ordine desc)
                -(goals_for[team] - goals_against[team]),  # Diff reti
                -goals_for[team],  # Gol fatti
                -total_scores[team]  # Punteggio fantacalcio totale
            )

        return sorted(teams, key=sort_key)

    def _print_result_box(self, result: Dict, aggregate_stats: Dict, my_team: str, result_type: str, total_sims: int):
        """
        Stampa un box colorato con il MIGLIOR o PEGGIOR risultato possibile

        Args:
            result: Dict con final_position e total_points
            aggregate_stats: Statistiche aggregate per contesto
            my_team: Nome della tua squadra
            result_type: 'best' o 'worst'
            total_sims: Numero totale di simulazioni
        """
        # Colori ANSI
        if result_type == 'best':
            color_start = '\033[92m'  # Verde
            title = "🏆 MIGLIOR RISULTATO POSSIBILE"
            border = '═'
            subtitle = "La migliore posizione raggiunta in tutte le simulazioni"
        else:
            color_start = '\033[91m'  # Rosso
            title = "⚠️  PEGGIOR RISULTATO POSSIBILE"
            border = '═'
            subtitle = "La peggiore posizione raggiunta in tutte le simulazioni"

        color_end = '\033[0m'  # Reset

        # Calcola la probabilità di arrivare in questa posizione specifica
        position_dist = aggregate_stats.get('position_distribution', {})
        prob_this_position = position_dist.get(result['final_position'], 0)

        # Costruisci il box
        width = 80
        print(f"\n{color_start}")
        print(border * width)
        print(f"{title:^{width}}")
        print(f"{subtitle:^{width}}")
        print(border * width)
        print()
        print(f"  🎯 RISULTATO:")
        print(f"      Posizione Finale:   {result['final_position']}°")
        if result.get('total_points'):
            print(f"      Punteggio Totale:   {result['total_points']:.1f}")
        print()
        print(f"  📊 PROBABILITÀ:")
        print(f"      Arrivare {result['final_position']}°: {prob_this_position:.1f}%")
        print(f"      (su {total_sims} simulazioni totali)")
        print()
        print(border * width)
        print(f"{color_end}")

    def _print_scenario_box(self, scenario: Dict, my_team: str, scenario_type: str):
        """
        Stampa un box colorato con i dati dello scenario migliore (verde) o peggiore (rosso)

        Args:
            scenario: Dati completi dello scenario
            my_team: Nome della tua squadra
            scenario_type: 'best' o 'worst'
        """
        my_stats = scenario['statistics'][my_team]

        # Calcola best/worst position dai dati raw
        my_positions = scenario.get('my_team_positions_raw', [])
        best_pos = min(my_positions) if my_positions else 1
        worst_pos = max(my_positions) if my_positions else 10

        my_points = scenario.get('my_team_points_raw', [])
        min_pts = min(my_points) if my_points else 0
        max_pts = max(my_points) if my_points else 0

        # Colori ANSI
        if scenario_type == 'best':
            color_start = '\033[92m'  # Verde
            title = "🏆 SCENARIO MIGLIORE"
            border = '═'
        else:
            color_start = '\033[91m'  # Rosso
            title = "⚠️  SCENARIO PEGGIORE"
            border = '═'

        color_end = '\033[0m'  # Reset

        # Costruisci il box
        width = 80
        print(f"\n{color_start}")
        print(border * width)
        print(f"{title:^{width}}")
        print(f"Scenario #{scenario['scenario_id']}")
        print(border * width)
        print()
        print(f"  📊 POSIZIONAMENTO:")
        print(f"      Posizione Media:    {my_stats['mean_position']:.1f}°")
        print(f"      Posizione Mediana:  {int(my_stats['median_position'])}°")
        print(f"      Migliore:           {best_pos}°")
        print(f"      Peggiore:           {worst_pos}°")
        print()
        print(f"  💯 PUNTEGGI:")
        print(f"      Media Punti:        {my_stats['mean_points']:.1f}")
        print(f"      Mediana Punti:      {my_stats['median_points']:.1f}")
        print(f"      Range:              {min_pts:.1f} - {max_pts:.1f}")
        print()
        print(f"  🎯 PROBABILITÀ:")
        print(f"      Vincere:            {my_stats['probability_win']:.1f}%")
        print(f"      Top 3 (Podio):      {my_stats['probability_top3']:.1f}%")
        print(f"      Top 6:              {my_stats['probability_top6']:.1f}%")
        print()
        print(f"  📈 DISTRIBUZIONE POSIZIONI (Top 5):")

        # Mostra le top 5 posizioni più probabili
        sorted_positions = sorted(
            my_stats['position_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for pos, prob in sorted_positions:
            bar_length = int(prob / 2)  # Scala per visualizzazione
            bar = '█' * bar_length
            print(f"      {pos}°:  {bar} {prob:.1f}%")

        print()
        print(border * width)
        print(f"{color_end}")

    def _format_scenario_summary(self, scenario: Dict, my_team: str, scenario_type: str) -> Dict:
        """
        Formatta un riepilogo compatto dello scenario migliore o peggiore

        Args:
            scenario: Dati completi dello scenario
            my_team: Nome della tua squadra
            scenario_type: 'best' o 'worst'

        Returns:
            Dict con i dati più significativi per la visualizzazione
        """
        my_stats = scenario['statistics'][my_team]

        # Calcola best/worst position dai dati raw
        my_positions = scenario.get('my_team_positions_raw', [])
        best_pos = int(min(my_positions)) if my_positions else 1
        worst_pos = int(max(my_positions)) if my_positions else 10

        my_points = scenario.get('my_team_points_raw', [])
        min_pts = round(min(my_points), 1) if my_points else 0
        max_pts = round(max(my_points), 1) if my_points else 0

        return {
            'scenario_id': scenario['scenario_id'],
            'type': scenario_type,
            'mean_position': round(my_stats['mean_position'], 1),
            'median_position': int(my_stats['median_position']),
            'best_position': best_pos,
            'worst_position': worst_pos,
            'mean_points': round(my_stats['mean_points'], 1),
            'median_points': round(my_stats['median_points'], 1),
            'min_points': min_pts,
            'max_points': max_pts,
            'probability_win': round(my_stats['probability_win'], 1),
            'probability_top3': round(my_stats['probability_top3'], 1),
            'probability_top6': round(my_stats['probability_top6'], 1),
            'position_distribution': {
                str(k): round(v, 1)
                for k, v in sorted(my_stats['position_distribution'].items())
            }
        }

    def _aggregate_scenarios(self, scenarios: List[Dict], my_team: str) -> Dict:
        """
        Aggrega statistiche su tutti gli scenari (3000 simulazioni totali)
        """
        print(f"\n[Monte Carlo] Aggregazione statistiche per {my_team}...")
        all_positions = []
        all_points = []

        for idx, scenario in enumerate(scenarios, 1):
            print(f"  [Aggregate] Scenario {idx}/{len(scenarios)}")
            my_stats = scenario['statistics'][my_team]

            # Usa i risultati reali quando disponibili.
            raw_positions = scenario.get('my_team_positions_raw')
            raw_points = scenario.get('my_team_points_raw')

            if raw_positions:
                all_positions.extend(raw_positions)
            else:
                for position, probability in my_stats['position_distribution'].items():
                    count = int(probability / 100 * scenario['n_simulations'])
                    all_positions.extend([position] * count)

            if raw_points:
                all_points.extend(raw_points)
            else:
                # Fallback compatibile con eventuali vecchi risultati.
                mean_pts = my_stats['mean_points']
                std_pts = my_stats['std_points']
                points_sample = self.rng.normal(
                    mean_pts,
                    std_pts,
                    scenario['n_simulations']
                )
                all_points.extend(points_sample)

        # Statistiche aggregate
        position_counts = {}
        for pos in all_positions:
            position_counts[pos] = position_counts.get(pos, 0) + 1

        n_total = len(all_positions)
        position_distribution = {
            pos: count / n_total * 100
            for pos, count in position_counts.items()
        }

        return {
            'mean_position': np.mean(all_positions),
            'median_position': np.median(all_positions),
            'position_distribution': position_distribution,
            'mean_points': np.mean(all_points),
            'median_points': np.median(all_points),
            'std_points': np.std(all_points),
            'min_points': np.min(all_points),
            'max_points': np.max(all_points),
            'probability_win': position_distribution.get(1, 0),
            'probability_top3': sum(position_distribution.get(i, 0) for i in range(1, 4)),
            'probability_top6': sum(position_distribution.get(i, 0) for i in range(1, 7)),
            'total_simulations': n_total
        }
