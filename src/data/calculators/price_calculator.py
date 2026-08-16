"""
Modulo principale per il calcolo della percentuale di prezzo massimo consigliato per i giocatori
Formula con percentili interni, fattore competitivo, bonus scarsità, clean sheets e FM scarsità
"""
import pandas as pd
from functools import lru_cache
from src.config import DEFAULT_AUCTION_BUDGET
from src.data.price_formula_config import ROLE_BUDGET_DISTRIBUTION, ROLE_STAT_WEIGHTS
from src.data.calculators.stats_extractor import StatsExtractor
from src.data.calculators.modifiers import PriceModifiers


class PriceCalculator:
    """Calcola la percentuale di budget consigliata per ogni giocatore"""

    def __init__(self, all_players_df=None, use_optimized=True):
        """
        Args:
            all_players_df: DataFrame con tutti i giocatori (opzionale)
            use_optimized: Se True, usa l'algoritmo ottimizzato per ruolo (default: True)
        """
        self.all_players_df = all_players_df
        self.percentiles_cache = {}
        self.price_cache = {}  # Cache per prezzi: {(player_id, budget): result}
        self.use_optimized = use_optimized
        self.optimized_calculator = None

        # Inizializza helper classes
        self.stats_extractor = StatsExtractor()
        self.modifiers = PriceModifiers(self.stats_extractor)

        self._build_percentile_rankings()

        # Inizializza algoritmo ottimizzato se richiesto
        if self.use_optimized and all_players_df is not None:
            try:
                from src.data.calculators.optimized_price_calculator import OptimizedPriceCalculator
                self.optimized_calculator = OptimizedPriceCalculator(all_players_df)
            except Exception:
                self.use_optimized = False

    def update_players_data(self, all_players_df):
        """
        Aggiorna il DataFrame dei giocatori e invalida la cache

        Args:
            all_players_df: Nuovo DataFrame con i giocatori
        """
        self.all_players_df = all_players_df
        self.percentiles_cache = {}
        self.price_cache = {}  # Invalida anche la cache prezzi
        self._build_percentile_rankings()

        # Reinizializza algoritmo ottimizzato se abilitato
        if self.use_optimized:
            try:
                from src.data.calculators.optimized_price_calculator import OptimizedPriceCalculator
                self.optimized_calculator = OptimizedPriceCalculator(all_players_df)
            except Exception:
                self.use_optimized = False
        self._build_percentile_rankings()

    def calculate_price_percentage(self, player_id, budget_total=DEFAULT_AUCTION_BUDGET):
        """
        Calcola la percentuale di budget consigliata per un giocatore (con cache)

        Formula: Percentuale = Score_Base × Team_Coeff × Presence × Trend × Competitivo × Scarsità × FM_Scarsità

        Args:
            player_id: ID del giocatore
            budget_total: Budget totale dell'asta (default 500)

        Returns:
            dict con percentage, credits, budget e breakdown dettagliato
        """
        # Controllo cache
        cache_key = (player_id, budget_total)
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]

        result = self._calculate_single_price(player_id, budget_total)

        # Salva in cache
        self.price_cache[cache_key] = result
        return result

    def calculate_batch_prices(self, player_ids, budget_total=DEFAULT_AUCTION_BUDGET):
        """
        Calcola prezzi per un batch di giocatori (usa cache quando possibile)

        Args:
            player_ids: Lista di ID giocatori
            budget_total: Budget totale dell'asta

        Returns:
            dict {player_id: price_data}
        """
        results = {}
        for player_id in player_ids:
            results[player_id] = self.calculate_price_percentage(player_id, budget_total)
        return results

    def _calculate_single_price(self, player_id, budget_total):
        """Calcolo effettivo del prezzo (senza cache)"""
        # Usa algoritmo ottimizzato se disponibile
        if self.use_optimized and self.optimized_calculator is not None:
            try:
                return self.optimized_calculator.calculate_price_percentage(player_id, budget_total)
            except Exception:
                # Fallback su algoritmo classico in caso di errore
                pass

        # Algoritmo classico
        if self.all_players_df is None or self.all_players_df.empty:
            return self._default_result()

        player_data = self.all_players_df[self.all_players_df['Id'] == player_id]
        if player_data.empty:
            return self._default_result()

        player_row = player_data.iloc[0]
        role = self.stats_extractor.extract_base_role(player_row['R'])
        team = player_row.get('Squadra', 'Unknown')
        player_name = player_row.get('Nome', '')

        # 1. Score base dalle statistiche
        base_score = self._calculate_direct_score(player_row, role)

        # 2. Coefficiente squadra (ridotto impatto)
        team_coeff = self.modifiers.get_team_coefficient(team)

        # 3. Bonus gol fatti/subiti squadra (NUOVO)
        team_performance = self.modifiers.get_team_performance_bonus(team, role)

        # 4. Modificatore presenze
        presence_mod = self.modifiers.get_presence_modifier(player_row, role)

        # 5. Modificatore trend
        trend_modifier, trend_symbol = self.modifiers.get_trend_modifier(player_row, role)

        # 6. Fattore competitivo
        competitive_factor = self.modifiers.get_competitive_factor(
            player_id, role, self.percentiles_cache
        )

        # 7. Bonus scarsità
        scarcity_bonus = self.modifiers.get_scarcity_bonus(player_row, role)

        # 8. Bonus FM scarsità
        fm_bonus = self.modifiers.get_fm_scarcity_bonus(player_row, role)

        # 9. Bonus titolarità
        titolarita_bonus = self.modifiers.get_titolarita_bonus(player_name)

        # 10. Bonus ranking scorsa stagione - ADDITIVO (NUOVO)
        ranking_bonus = self.modifiers.get_ranking_bonus(player_name)

        # 11. Bonus rigorista - ADDITIVO
        rigorista_bonus = self.modifiers.get_rigorista_bonus(player_name)

        # 12. Bonus tiratore punizioni - ADDITIVO
        tiratore_bonus = self.modifiers.get_tiratore_bonus(player_name)

        # Calcolo finale: moltiplicatori + additivi
        final_percentage = ((base_score * team_coeff * team_performance * presence_mod *
                           trend_modifier * competitive_factor *
                           scarcity_bonus * fm_bonus * titolarita_bonus) +
                          ranking_bonus + rigorista_bonus + tiratore_bonus)

        # Clamp nel range del ruolo
        role_config = ROLE_BUDGET_DISTRIBUTION[role]
        min_pct, max_pct = role_config['range']
        final_percentage = max(min_pct, min(max_pct, final_percentage))

        # Calcola crediti
        suggested_price = int(round(final_percentage * budget_total / 100))

        result = {
            'percentage': round(final_percentage, 1),
            'credits': suggested_price,
            'budget': budget_total,
            'breakdown': {
                'base_score': round(base_score, 1),
                'team_coefficient': team_coeff,
                'team_name': team,
                'team_performance': team_performance,
                'presence_modifier': presence_mod,
                'trend_modifier': trend_modifier,
                'trend_symbol': trend_symbol,
                'competitive_factor': competitive_factor,
                'scarcity_bonus': scarcity_bonus,
                'fm_scarcity_bonus': fm_bonus,
                'titolarita_bonus': titolarita_bonus,
                'ranking_bonus': ranking_bonus,
                'rigorista_bonus': rigorista_bonus,
                'tiratore_bonus': tiratore_bonus,
                'final': round(final_percentage, 1),
                'role_range': f"{min_pct}%-{max_pct}%"
            }
        }

        return result

    def _calculate_direct_score(self, player_row, role):
        """
        Calcola score diretto dalle statistiche con i pesi configurati

        Args:
            player_row: Serie pandas con i dati del giocatore
            role: Ruolo del giocatore

        Returns:
            float: Score base
        """
        if role not in ROLE_STAT_WEIGHTS:
            return ROLE_BUDGET_DISTRIBUTION.get(role, {}).get('avg_per_player', 5.0)

        weights = ROLE_STAT_WEIGHTS[role]
        score = 0.0

        for stat, weight in weights.items():
            if weight == 0:
                continue

            value = self.stats_extractor.get_numeric_stat(player_row, stat, role)
            if value is None:
                continue

            # Applica peso direttamente al valore
            score += value * weight

        # Assicura un minimo
        role_config = ROLE_BUDGET_DISTRIBUTION[role]
        min_score = role_config['range'][0]

        return max(min_score, score)

    def _build_percentile_rankings(self):
        """Costruisce le classifiche interne per Gol e Assist per ruolo"""
        if self.all_players_df is None or self.all_players_df.empty:
            return

        # Calcola percentili per ogni ruolo
        for role in ['P', 'D', 'C', 'A']:
            role_players = self.all_players_df[
                self.all_players_df['R'].str.startswith(role)
            ].copy()

            if role_players.empty:
                continue

            # Calcola percentili per Gf, Ass, Rp
            for stat in ['Gf', 'Ass', 'Rp']:
                col_name = f'{stat}_weighted'
                if col_name not in role_players.columns:
                    continue

                # Estrai valori numerici
                role_players[f'{stat}_numeric'] = role_players[col_name].apply(
                    self.stats_extractor.extract_number
                )
                role_players[f'{stat}_numeric'] = role_players[f'{stat}_numeric'].fillna(0)

                # Calcola percentile (0-100)
                role_players[f'{stat}_percentile'] = role_players[f'{stat}_numeric'].rank(pct=True) * 100

                # Salva nella cache
                for _, player in role_players.iterrows():
                    player_id = player['Id']
                    cache_key = f"{player_id}_{stat}"
                    self.percentiles_cache[cache_key] = player[f'{stat}_percentile']

    def _default_result(self):
        """Risultato di default quando il giocatore non viene trovato"""
        return {
            'percentage': 1.0,
            'credits': 1,
            'budget': DEFAULT_AUCTION_BUDGET,
            'breakdown': {
                'base_score': 1.0,
                'team_coefficient': 1.0,
                'team_name': 'Unknown',
                'presence_modifier': 1.0,
                'trend_modifier': 1.0,
                'trend_symbol': '',
                'competitive_factor': 1.0,
                'scarcity_bonus': 1.0,
                'fm_scarcity_bonus': 1.0,
                'final': 1.0,
                'role_range': '1%-25%'
            }
        }

    def calculate_suggested_price(self, percentage, budget_total):
        """
        Calcola il prezzo in crediti da una percentuale

        Args:
            percentage: Percentuale del budget
            budget_total: Budget totale

        Returns:
            int: Prezzo suggerito in crediti
        """
        return int(round(percentage * budget_total / 100))
