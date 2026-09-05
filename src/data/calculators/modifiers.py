"""
Modulo per il calcolo dei modificatori di prezzo
Include bonus per titolarità, rigoristi, tiratori punizioni, ranking e gol squadra
"""
import json
import os
from src.config import TREND_MODIFIERS
from src.data.price_formula_config import PRESENCE_THRESHOLDS, TEAM_COEFFICIENTS
from src.data.competitive_factors import COMPETITIVE_FACTOR, SCARCITY_BONUS, get_fm_scarcity_bonus
from src.data.titolarita_loader import load_titolarita_map
from src.data.season_standings import load_previous_season_standings
from src.data.stats_loader import StatsLoader
import pandas as pd


class PriceModifiers:
    """Calcola i vari modificatori che influenzano il prezzo"""

    def __init__(self, stats_extractor):
        """
        Args:
            stats_extractor: Istanza di StatsExtractor per estrarre valori
        """
        self.stats_extractor = stats_extractor
        self._titolarita_map = None
        self._rigoristi_map = None
        self._tiratori_map = None
        self._role_rankings = None

    def _load_tiratori_data(self):
        """Carica i dati dei rigoristi e tiratori (con cache)"""
        if self._rigoristi_map is not None:
            return self._rigoristi_map, self._tiratori_map

        tiratori_file = os.path.join('data', 'Tiratori', 'tiratori.json')
        rigoristi_map = {}
        tiratori_map = {}

        if not os.path.exists(tiratori_file):
            self._rigoristi_map = rigoristi_map
            self._tiratori_map = tiratori_map
            return rigoristi_map, tiratori_map

        try:
            with open(tiratori_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                for team_data in data:
                    # Rigoristi
                    rigoristi = team_data.get('rigoristi', {})
                    for key, nome in rigoristi.items():
                        if '1_rigorista' in key:
                            rigoristi_map[nome] = 1
                            rigoristi_map[nome + ' *'] = 1
                        elif '2_rigorista' in key:
                            rigoristi_map[nome] = 2
                            rigoristi_map[nome + ' *'] = 2
                        elif '3_rigorista' in key:
                            rigoristi_map[nome] = 3
                            rigoristi_map[nome + ' *'] = 3

                    # Tiratori piazzati
                    piazzati = team_data.get('piazzati_e_angoli', {})
                    for key, nome in piazzati.items():
                        if '1_tiratore' in key:
                            tiratori_map[nome] = 1
                            tiratori_map[nome + ' *'] = 1
                        elif '2_tiratore' in key:
                            tiratori_map[nome] = 2
                            tiratori_map[nome + ' *'] = 2
                        elif '3_tiratore' in key:
                            tiratori_map[nome] = 3
                            tiratori_map[nome + ' *'] = 3
        except Exception:
            pass

        self._rigoristi_map = rigoristi_map
        self._tiratori_map = tiratori_map
        return rigoristi_map, tiratori_map

    def _calculate_role_rankings(self):
        """Calcola il ranking per ruolo della stagione scorsa (con cache)"""
        if self._role_rankings is not None:
            return self._role_rankings

        stats_loader = StatsLoader()
        stats_data = stats_loader.load_all_stats()

        if not stats_data or 'recent' not in stats_data:
            self._role_rankings = {}
            return {}

        season_df = stats_data['recent']['df'].reset_index()

        # Converti colonne numeriche
        numeric_cols = ['Pv', 'Fm', 'Gf', 'Ass']
        for col in numeric_cols:
            if col in season_df.columns:
                season_df[col] = pd.to_numeric(season_df[col], errors='coerce')

        # Filtra giocatori con almeno 20 presenze
        qualified = season_df[season_df['Pv'] >= 20].copy()

        rankings = {}

        for role in ['P', 'D', 'C', 'A']:
            role_players = qualified[qualified['R'].str.startswith(role)].copy()

            if role_players.empty:
                continue

            # Calcola uno score combinato
            role_players['combined_score'] = (
                role_players['Fm'] * 10 +
                role_players['Gf'] * 5 +
                role_players['Ass'] * 3
            )

            role_players = role_players.sort_values('combined_score', ascending=False)

            for idx, (_, player) in enumerate(role_players.head(30).iterrows()):
                player_name = player['Nome']
                rankings[player_name] = {
                    'role': role,
                    'rank': idx + 1,
                    'fm': player['Fm'],
                    'gf': player['Gf'],
                    'ass': player['Ass'],
                    'score': player['combined_score']
                }

        self._role_rankings = rankings
        return rankings

    def _extract_titolarita_percentage(self, titolarita_str):
        """Estrae il valore numerico da '85%' -> 85.0"""
        if not titolarita_str or titolarita_str == '-':
            return 0.0
        try:
            return float(titolarita_str.replace('%', ''))
        except:
            return 0.0

    def get_team_coefficient(self, team):
        """
        Ottiene il coefficiente squadra (bilanciato con classifica)

        Args:
            team: Nome della squadra

        Returns:
            float: Coefficiente moltiplicativo
        """
        base_coeff = TEAM_COEFFICIENTS.get(team, 0.80)
        standings = load_previous_season_standings()
        standing = standings.get(team)

        if standing:
            participants = standing['participants']
            position = standing['position']
            normalized_rank = (participants - position) / max(participants - 1, 1)
            classifica_bonus = 0.85 + normalized_rank * 0.30
        else:
            classifica_bonus = 0.90

        # Media pesata: 60% base_coeff, 40% classifica
        combined = base_coeff * 0.6 + classifica_bonus * 0.4

        return combined

    def get_team_performance_bonus(self, team, role):
        """
        Bonus basato su gol fatti/subiti della squadra scorsa stagione

        Args:
            team: Nome squadra
            role: Ruolo giocatore

        Returns:
            float: Moltiplicatore performance (0.92-1.06)
        """
        standings = load_previous_season_standings()
        data = standings.get(team)
        if not data:
            return 1.0

        gf = data['gf']
        gs = data['gs']

        # Bonus attacco (per C e A)
        if gf >= 70:
            offensive_mult = 1.12
        elif gf >= 60:
            offensive_mult = 1.08
        elif gf >= 50:
            offensive_mult = 1.04
        elif gf >= 40:
            offensive_mult = 1.0
        else:
            offensive_mult = 0.94

        # Bonus difesa (per P e D)
        if gs <= 30:
            defensive_mult = 1.12
        elif gs <= 35:
            defensive_mult = 1.08
        elif gs <= 40:
            defensive_mult = 1.04
        elif gs <= 50:
            defensive_mult = 1.0
        else:
            defensive_mult = 0.92

        # Riduci impatto al 50%
        offensive_mult = 1.0 + (offensive_mult - 1.0) * 0.5
        defensive_mult = 1.0 + (defensive_mult - 1.0) * 0.5

        if role in ['C', 'A']:
            return offensive_mult
        elif role in ['P', 'D']:
            return defensive_mult
        else:
            return 1.0

    def get_titolarita_bonus(self, player_name):
        """
        Calcola bonus basato sulla percentuale di titolarità

        Args:
            player_name: Nome del giocatore

        Returns:
            float: Moltiplicatore titolarità (0.55-1.22)
        """
        if self._titolarita_map is None:
            self._titolarita_map = load_titolarita_map()

        titolarita_str = self._titolarita_map.get(player_name, '-')
        titolarita_pct = self._extract_titolarita_percentage(titolarita_str)

        if titolarita_pct >= 85:
            return 1.25
        elif titolarita_pct >= 70:
            return 1.16
        elif titolarita_pct >= 50:
            return 1.0
        elif titolarita_pct >= 30:
            return 0.78
        else:
            return 0.50

    def get_ranking_bonus(self, player_name):
        """
        Bonus ADDITIVO basato sul ranking scorsa stagione

        Args:
            player_name: Nome del giocatore

        Returns:
            float: Bonus percentuale assoluto (0-3.5%)
        """
        rankings = self._calculate_role_rankings()

        if player_name not in rankings:
            return 0.0

        rank = rankings[player_name]['rank']

        if rank == 1:  # Migliore del ruolo
            return 3.5
        elif rank <= 3:  # Top 3
            return 2.2
        elif rank <= 5:  # Top 5
            return 1.4
        elif rank <= 10:  # Top 10
            return 0.7
        elif rank <= 15:  # Top 15
            return 0.4
        elif rank <= 25:  # Top 25
            return 0.15
        else:
            return 0.0

    def get_rigorista_bonus(self, player_name):
        """
        Calcola bonus ADDITIVO per rigoristi

        Args:
            player_name: Nome del giocatore

        Returns:
            float: Bonus percentuale assoluto (0-2.8%)
        """
        rigoristi_map, _ = self._load_tiratori_data()
        rigorista_pos = rigoristi_map.get(player_name, 0)

        if rigorista_pos == 1:
            return 2.8
        elif rigorista_pos == 2:
            return 1.4
        elif rigorista_pos == 3:
            return 0.7
        else:
            return 0.0

    def get_tiratore_bonus(self, player_name):
        """
        Calcola bonus ADDITIVO per tiratori punizioni (RIDOTTO)

        Args:
            player_name: Nome del giocatore

        Returns:
            float: Bonus percentuale assoluto (0-0.8%)
        """
        _, tiratori_map = self._load_tiratori_data()
        tiratore_pos = tiratori_map.get(player_name, 0)

        if tiratore_pos == 1:
            return 0.8  # Ridotto da 1.6
        elif tiratore_pos == 2:
            return 0.4  # Ridotto da 0.9
        elif tiratore_pos == 3:
            return 0.2  # Ridotto da 0.4
        else:
            return 0.0

    def get_presence_modifier(self, player_row, role):
        """
        Calcola modificatore basato sulle presenze

        Args:
            player_row: Serie pandas con i dati del giocatore
            role: Ruolo del giocatore

        Returns:
            float: Modificatore presenza (0.78-1.05)
        """
        pv = self.stats_extractor.extract_number(player_row.get('Pv_weighted', 0))

        if pv is None:
            return 1.0

        if pv >= 28:
            return 1.05
        elif pv >= 20:
            return 1.0
        elif pv >= 15:
            return 0.92
        else:
            return 0.78

    def get_trend_modifier(self, player_row, role):
        """
        Estrae il modificatore trend dalle statistiche chiave

        Args:
            player_row: Serie pandas con i dati del giocatore
            role: Ruolo del giocatore

        Returns:
            tuple: (modifier_value, trend_symbol)
        """
        # Cerca trend in Fm (principale indicatore)
        fm_col = 'Fm_weighted'
        if fm_col in player_row.index:
            value = str(player_row[fm_col])
            for symbol, modifier in TREND_MODIFIERS.items():
                if symbol in value:
                    return modifier, symbol

        return 1.0, ''

    def get_competitive_factor(self, player_id, role, percentile_cache):
        """
        Calcola il fattore competitivo basato sul percentile
        I top player (percentile 90+) valgono molto di più in un'asta a 10 persone

        Args:
            player_id: ID del giocatore
            role: Ruolo del giocatore
            percentile_cache: Cache dei percentili

        Returns:
            float: Fattore competitivo (1.0-1.12)
        """
        # Usa il percentile della statistica principale per il ruolo
        main_stat = {
            'P': 'Rp',  # Rigori parati
            'D': 'Gf',  # Goal
            'C': 'Gf',  # Goal
            'A': 'Gf'   # Goal
        }.get(role, 'Gf')

        cache_key = f"{player_id}_{main_stat}"
        percentile = percentile_cache.get(cache_key, 50.0)

        # Determina il fattore
        if percentile >= 95:
            return COMPETITIVE_FACTOR['percentile_95_100']
        elif percentile >= 90:
            return COMPETITIVE_FACTOR['percentile_90_95']
        elif percentile >= 80:
            return COMPETITIVE_FACTOR['percentile_80_90']
        elif percentile >= 70:
            return COMPETITIVE_FACTOR['percentile_70_80']
        else:
            return COMPETITIVE_FACTOR['percentile_0_70']

    def get_scarcity_bonus(self, player_row, role):
        """
        Bonus scarsità: pochi giocatori forti = valgono di più
        Es: solo 5-6 attaccanti segnano 10+ gol, quindi competizione feroce

        Args:
            player_row: Serie pandas con i dati del giocatore
            role: Ruolo del giocatore

        Returns:
            float: Bonus scarsità (1.0-1.22)
        """
        if role not in SCARCITY_BONUS:
            return 1.0

        config = SCARCITY_BONUS[role]
        stat = config['top_stat']
        value = self.stats_extractor.get_numeric_stat(player_row, stat, role)

        if value is None:
            return 1.0

        # Trova la soglia appropriata
        for threshold, bonus in config['thresholds']:
            if value >= threshold:
                return bonus

        return 1.0

    def get_fm_scarcity_bonus(self, player_row, role):
        """
        Bonus scarsità per Fantamedia alta (portieri FM>6.5 sono rarissimi)

        Args:
            player_row: Serie pandas con i dati del giocatore
            role: Ruolo del giocatore

        Returns:
            float: Bonus FM scarsità (1.0-1.35)
        """
        fm = self.stats_extractor.extract_number(player_row.get('Fm_weighted', 0))

        if fm is None:
            return 1.0

        return get_fm_scarcity_bonus(role, fm)
