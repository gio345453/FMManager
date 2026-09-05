"""
Recommendation service - implementa l'algoritmo di suggerimento del terzo giocatore
Usa ESATTAMENTE la logica da src/ui/player_comparison.py linee 602-744
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.calculators.price_calculator import PriceCalculator


class RecommendationService:
    """Service per suggerimenti giocatori basato su similarità"""

    def __init__(self, df_with_overall, price_calculator=None):
        """
        Inizializza service con DataFrame giocatori

        Args:
            df_with_overall: DataFrame con tutti i giocatori e Overall scores
            price_calculator: PriceCalculator instance per calcolo prezzi
        """
        self.all_players = df_with_overall
        self.price_calculator = price_calculator or PriceCalculator(
            all_players_df=df_with_overall,
            use_optimized=True
        )

    def _safe_float(self, value) -> float:
        """Converte un valore in float gestendo NaN e simboli trend"""
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        # Rimuovi simboli trend
        value_str = str(value).replace('↑', '').replace('↓', '').replace('→', '').strip()
        try:
            return float(value_str)
        except:
            return 0.0

    def get_recommended_players(
        self,
        selected_player_ids: List[int],
        budget: float = 500,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggerisci giocatori simili basandosi sui giocatori già selezionati

        Algoritmo IDENTICO a _show_recommended_players in player_comparison.py:
        - Se nessun giocatore selezionato: top 5 per Overall
        - Se giocatori selezionati: calcola similarità basata su ruolo, FM, prezzo, PV

        Args:
            selected_player_ids: Lista ID giocatori già selezionati (0-2 giocatori)
            budget: Budget per calcolo prezzi
            limit: Numero massimo di raccomandazioni (default 5)

        Returns:
            Lista di giocatori raccomandati con score di similarità
        """
        # Caso 1: Nessun giocatore selezionato - mostra top 5 per Overall
        if not selected_player_ids or len(selected_player_ids) == 0:
            filtered = self.all_players.copy()
            filtered['_overall_sort'] = pd.to_numeric(filtered['Overall'], errors='coerce')
            filtered = filtered.sort_values('_overall_sort', ascending=False, na_position='last').head(limit)

            recommendations = []
            for _, row in filtered.iterrows():
                player_id = int(row['Id'])
                # Calcola prezzo usando PriceCalculator
                price_data = self.price_calculator.calculate_price_percentage(player_id, budget)

                recommendations.append({
                    'id': player_id,
                    'nome': str(row['Nome']),
                    'squadra': str(row['Squadra']),
                    'ruolo': str(row['R']),
                    'overall': int(row['Overall']) if pd.notna(row['Overall']) and row['Overall'] != 'N/A' else None,
                    'fm_weighted': self._safe_float(row.get('Fm_weighted')),
                    'mv_weighted': self._safe_float(row.get('Mv_weighted')),
                    'price_percentage': float(price_data.get('percentage', 0)),
                    'price_credits': float(price_data.get('credits', 0)),
                    'similarity_score': None
                })

            return recommendations

        # Caso 2: Giocatori selezionati - calcola similarità
        # Carica dati dei giocatori selezionati
        selected_players = []
        for player_id in selected_player_ids[:2]:  # Max 2 giocatori per calcolo target
            player_row = self.all_players[self.all_players['Id'] == player_id]
            if not player_row.empty:
                selected_players.append(player_row.iloc[0].to_dict())

        if len(selected_players) == 0:
            # Fallback: top 5 per Overall
            return self.get_recommended_players([], budget, limit)

        # Estrai caratteristiche dai giocatori selezionati
        roles = []
        fm_values = []
        price_values = []
        pv_values = []

        for player in selected_players:
            role_full = player.get('R', '')
            role_base = role_full.split('/')[0].split('(')[0].strip()
            roles.append(role_base)

            fm_values.append(self._safe_float(player.get('Fm_weighted', 6.0)))
            price_values.append(self._safe_float(player.get('price_percentage', 5.0)))
            pv_values.append(self._safe_float(player.get('Pv_weighted', 20)))

        # Calcola target medio
        target_role = roles[0] if len(set(roles)) == 1 else None
        target_fm = sum(fm_values) / len(fm_values)
        target_price = sum(price_values) / len(price_values)
        target_pv = sum(pv_values) / len(pv_values)

        # Filtra candidati
        candidates = self.all_players.copy()

        # Escludi giocatori già selezionati
        candidates = candidates[~candidates['Id'].isin(selected_player_ids)]

        # Calcola score di similarità per ogni candidato
        scores = []

        for idx, row in candidates.iterrows():
            score = 0.0

            # 1. RUOLO (peso massimo)
            role_full = row.get('R', '')
            role_base = role_full.split('/')[0].split('(')[0].strip()

            if target_role and role_base == target_role:
                score += 100  # Match perfetto ruolo
            elif target_role:
                continue  # Skip se ruolo diverso

            # 2. FM ultima stagione (40%)
            fm = self._safe_float(row.get('Fm_weighted', 6.0))
            fm_diff = abs(fm - target_fm)
            fm_score = max(0, 40 - (fm_diff * 20))
            score += fm_score

            # 3. Prezzo massimo (30%)
            price = self._safe_float(row.get('price_percentage', 5.0))
            price_diff = abs(price - target_price)
            price_score = max(0, 30 - (price_diff * 2))
            score += price_score

            # 4. PV ultima stagione (30%)
            pv = self._safe_float(row.get('Pv_weighted', 20))
            pv_diff = abs(pv - target_pv)
            pv_score = max(0, 30 - (pv_diff * 1.5))
            score += pv_score

            # 5. Ranking interno al ruolo (bonus)
            overall = self._safe_float(row.get('Overall', 50))
            ranking_bonus = overall / 10
            score += ranking_bonus

            scores.append((idx, score))

        # Ordina per score e prendi top N
        scores.sort(key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in scores[:limit]]

        recommended = candidates.loc[top_indices]

        # Formatta risultati
        recommendations = []
        score_map = {idx: score for idx, score in scores}

        for idx, row in recommended.iterrows():
            player_id = int(row['Id'])
            # Calcola prezzo usando PriceCalculator
            price_data = self.price_calculator.calculate_price_percentage(player_id, budget)

            recommendations.append({
                'id': player_id,
                'nome': str(row['Nome']),
                'squadra': str(row['Squadra']),
                'ruolo': str(row['R']),
                'overall': int(row['Overall']) if pd.notna(row['Overall']) and row['Overall'] != 'N/A' else None,
                'fm_weighted': self._safe_float(row.get('Fm_weighted')),
                'mv_weighted': self._safe_float(row.get('Mv_weighted')),
                'price_percentage': float(price_data.get('percentage', 0)),
                'price_credits': float(price_data.get('credits', 0)),
                'similarity_score': round(score_map.get(idx, 0), 2)
            })

        return recommendations
