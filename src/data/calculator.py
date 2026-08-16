"""
Modulo per il calcolo delle statistiche ponderate e degli Overall
"""
import pandas as pd
import numpy as np
from src.config import (
    NUMERIC_COLUMNS, ROLE_WEIGHTS, TREND_THRESHOLD,
    MIN_PARTITE_AFFIDABILI, PENALTY_THRESHOLDS, PENALTY_THRESHOLDS_BY_ROLE
)
from src.data.season_loader import CurrentSeasonLoader
from src.data.stats_loader import StatsLoader
from src.utils.data_utils import extract_base_role


class StatsCalculator:
    """Calcola statistiche ponderate e Overall scores"""

    def __init__(self):
        self.season_loader = CurrentSeasonLoader()
        self.stats_loader = StatsLoader()

    def calculate_trend(self, recent_value, middle_value, inverse=False):
        """
        Calcola il trend confrontando le due stagioni più recenti.

        Args:
            recent_value: Valore stagione recente
            middle_value: Valore stagione media
            inverse: True per statistiche dove meno è meglio (es. Gs per portieri)

        Returns:
            Stringa con simbolo trend (' ↑', ' ↓', ' →') o stringa vuota
        """
        if pd.isna(recent_value) or pd.isna(middle_value):
            return ''

        diff = recent_value - middle_value

        if inverse:
            diff = -diff

        if diff > TREND_THRESHOLD:
            return ' ↑'
        elif diff < -TREND_THRESHOLD:
            return ' ↓'
        else:
            return ' →'

    def calculate_weighted_stats(self):
        """
        Calcola le statistiche ponderate per tutti i giocatori.

        Returns:
            DataFrame con statistiche ponderate o None in caso di errore
        """
        # Carica stagione corrente
        current_players = self.season_loader.load_current_season()
        if current_players is None:
            return None

        # Carica tutte le statistiche storiche
        stats_data = self.stats_loader.load_all_stats()
        if not stats_data:
            return None

        weighted_players = []

        for _, player in current_players.iterrows():
            # Estrai info base giocatore
            player_info = self.season_loader.extract_player_info(player)
            player_id = player_info['Id']
            player_role = player_info['R']

            # Recupera statistiche da tutte le stagioni
            seasons_found, recent_stats, middle_stats, season_data = \
                self.stats_loader.get_player_stats(player_id, stats_data)

            # Prepara nome con asterisco se solo 1 stagione
            player_name = player_info['Nome']
            if seasons_found == 1:
                player_name = f"{player_name} *"

            # Formatta ruolo con eventuali ruoli multipli
            role_display = self.season_loader.format_role_display(
                player_role, player_info['RM']
            )

            player_data = {
                'Id': player_id,
                'Nome': player_name,
                'Squadra': player_info['Squadra'],
                'R': role_display,
                'seasons_count': seasons_found,
                'Pv_recent': recent_stats.get('Pv', np.nan) if recent_stats else np.nan
            }

            # Calcola statistiche ponderate
            for col in NUMERIC_COLUMNS:
                weighted_value = 0
                total_weight = 0

                for season_key, season_info in stats_data.items():
                    weight = season_info['weight']

                    if season_key in season_data:
                        player_row = season_data[season_key]
                        if col in player_row and pd.notna(player_row[col]):
                            weighted_value += player_row[col] * weight
                            total_weight += weight

                if seasons_found == 0:
                    player_data[f'{col}_weighted'] = 'N/A'
                elif total_weight > 0:
                    base_value = round(weighted_value / total_weight, 2)

                    trend = ''
                    if seasons_found >= 2 and col in recent_stats and col in middle_stats:
                        if player_role == 'P' and col == 'Gs':
                            trend = self.calculate_trend(recent_stats[col], middle_stats[col], inverse=True)
                        elif player_role != 'P' and col in ['Fm', 'Gf', 'Ass']:
                            trend = self.calculate_trend(recent_stats[col], middle_stats[col])

                    player_data[f'{col}_weighted'] = f"{base_value}{trend}" if trend else base_value
                else:
                    player_data[f'{col}_weighted'] = 'N/A'

            weighted_players.append(player_data)

        return pd.DataFrame(weighted_players)

    def calculate_overall_scores(self, df):
        """
        Calcola l'Overall score (1-99) per ogni giocatore basato sui percentili pesati per ruolo.

        Args:
            df: DataFrame con statistiche ponderate

        Returns:
            DataFrame con colonna Overall aggiunta
        """
        if df is None or df.empty:
            return df

        df_copy = df.copy()

        # Prepara colonne numeriche per il calcolo dei percentili
        numeric_stats = {}
        for col in NUMERIC_COLUMNS:
            col_name = f'{col}_weighted'
            if col_name in df_copy.columns:
                numeric_values = pd.to_numeric(
                    df_copy[col_name].astype(str).str.replace(r'[↑↓→]', '', regex=True),
                    errors='coerce'
                )
                numeric_stats[col] = numeric_values

        # Aggiungi Pv_recent per i portieri
        if 'Pv_recent' in df_copy.columns:
            numeric_stats['Pv_recent'] = pd.to_numeric(df_copy['Pv_recent'], errors='coerce')
        else:
            numeric_stats['Pv_recent'] = pd.Series([np.nan] * len(df_copy), index=df_copy.index)

        # Crea DataFrame temporaneo con valori numerici
        temp_df = pd.DataFrame(numeric_stats)

        # Calcola Gs per partita per i portieri usando operazioni vettoriali
        # Estrai ruoli base in modo vettoriale
        base_roles = df_copy['R'].apply(extract_base_role)
        portieri_mask = base_roles == 'P'

        # Calcola Gs_per_partita solo per i portieri
        temp_df['Gs_per_partita'] = np.nan
        if 'Gs' in temp_df.columns and 'Pv' in temp_df.columns:
            valid_pv_mask = portieri_mask & (temp_df['Pv'] > 0)
            temp_df.loc[valid_pv_mask, 'Gs_per_partita'] = (
                temp_df.loc[valid_pv_mask, 'Gs'] / temp_df.loc[valid_pv_mask, 'Pv']
            )

        # Filtra giocatori affidabili (min 15 partite) usando operazioni vettoriali
        pv_check = temp_df['Pv'].copy()
        pv_check[portieri_mask] = temp_df.loc[portieri_mask, 'Pv_recent']
        mask_affidabili = pv_check >= MIN_PARTITE_AFFIDABILI

        # Calcola percentili solo sui giocatori affidabili
        temp_df_affidabili = temp_df[mask_affidabili]

        percentiles = {}
        for col in temp_df.columns:
            valid_values = temp_df_affidabili[col].dropna()
            if len(valid_values) > 0:
                percentiles[col] = temp_df[col].rank(pct=True, method='average') * 100
                affidabili_ranks = temp_df_affidabili[col].rank(pct=True, method='average') * 100
                for idx in temp_df_affidabili.index:
                    if pd.notna(temp_df_affidabili.loc[idx, col]):
                        percentiles[col][idx] = affidabili_ranks[idx]
            else:
                percentiles[col] = pd.Series([50] * len(temp_df), index=temp_df.index)

        # Per Gs (gol subiti), inverti il percentile (meno è meglio)
        if 'Gs' in percentiles:
            # Crea percentile separato per Gs_per_partita (solo portieri)
            valid_values = temp_df_affidabili['Gs_per_partita'].dropna()
            if len(valid_values) > 0:
                gs_per_partita_ranks = temp_df['Gs_per_partita'].rank(pct=True, method='average') * 100
                affidabili_ranks = temp_df_affidabili['Gs_per_partita'].rank(pct=True, method='average') * 100
                for idx in temp_df_affidabili.index:
                    if pd.notna(temp_df_affidabili.loc[idx, 'Gs_per_partita']):
                        gs_per_partita_ranks[idx] = affidabili_ranks[idx]
                percentiles['Gs_per_partita'] = 100 - gs_per_partita_ranks

            percentiles['Gs'] = 100 - percentiles['Gs']

        # Calcola Overall per ogni giocatore usando operazioni vettoriali dove possibile
        overall_scores = []

        # Pre-calcola i ruoli base per tutti i giocatori
        base_roles_series = df_copy['R'].apply(extract_base_role)

        for idx, base_role in enumerate(base_roles_series):
            if base_role not in ROLE_WEIGHTS:
                overall_scores.append('N/A')
                continue

            weights = ROLE_WEIGHTS[base_role]
            weighted_sum = 0
            total_weight = 0

            for stat, weight in weights.items():
                # Per i portieri, usa Pv_recent invece di Pv e Gs_per_partita invece di Gs
                stat_to_use = stat
                if base_role == 'P':
                    if stat == 'Pv':
                        stat_to_use = 'Pv_recent'
                    elif stat == 'Gs':
                        stat_to_use = 'Gs_per_partita'

                if stat_to_use in percentiles and pd.notna(percentiles[stat_to_use].iloc[idx]):
                    weighted_sum += percentiles[stat_to_use].iloc[idx] * weight
                    total_weight += weight

            if total_weight > 0:
                base_overall = weighted_sum / total_weight

                # Applica penalità per basse presenze
                if base_role == 'P' and 'Pv_recent' in temp_df.columns:
                    pv_value = temp_df.iloc[idx]['Pv_recent']
                elif 'Pv' in temp_df.columns:
                    pv_value = temp_df.iloc[idx]['Pv']
                else:
                    pv_value = np.nan

                if pd.notna(pv_value):
                    # Usa penalità specifica per ruolo se disponibile
                    thresholds = PENALTY_THRESHOLDS_BY_ROLE.get(base_role, PENALTY_THRESHOLDS)

                    penalty = 1.0
                    for threshold, penalty_value in thresholds:
                        if pv_value < threshold:
                            penalty = penalty_value
                            break

                    base_overall *= penalty

                overall = int(round(base_overall))
                overall = max(1, min(99, overall))
                overall_scores.append(overall)
            else:
                overall_scores.append('N/A')

        df_copy['Overall'] = overall_scores

        # Normalizza gli Overall dei portieri per renderli comparabili con altri ruoli
        from src.data.normalizer import normalize_goalkeeper_overall
        df_copy = normalize_goalkeeper_overall(df_copy)

        return df_copy

    def get_price_calculator(self):
        """Restituisce il calcolatore prezzi ottimizzato"""
        # Calcola le stats ponderate se non già fatto
        if not hasattr(self, '_weighted_stats'):
            self._weighted_stats = self.calculate_weighted_stats()

        from src.data.calculators.optimized_price_calculator import OptimizedPriceCalculator
        return OptimizedPriceCalculator(self._weighted_stats)
