"""
Comparison service - wrappa PlayerComparisonLogic esistente
NON modifica le formule, usa direttamente la logica esistente
"""
from typing import List, Dict, Any, Optional
from src.logic.player_comparison_logic import PlayerComparisonLogic
from src.data.calculators.price_calculator import PriceCalculator


class ComparisonService:
    """Service layer per Player Comparison"""

    def __init__(self, df_with_overall):
        """
        Inizializza service con DataFrame giocatori

        Args:
            df_with_overall: DataFrame con tutti i giocatori e Overall scores
        """
        self.df_with_overall = df_with_overall
        self.comparison_logic = PlayerComparisonLogic()

    def compare_players(
        self,
        player_ids: List[int],
        budget: float = 500
    ) -> Dict[str, Any]:
        """
        Confronta 2-3 giocatori usando logica esistente

        Args:
            player_ids: Lista di 2-3 ID giocatori da confrontare
            budget: Budget totale per calcolo prezzi

        Returns:
            Dict con dati comparativi dei giocatori
        """
        if not player_ids or len(player_ids) < 2 or len(player_ids) > 3:
            raise ValueError("Devi fornire 2 o 3 player IDs per il confronto")

        # Inizializza PriceCalculator
        price_calculator = PriceCalculator(
            all_players_df=self.df_with_overall,
            use_optimized=True
        )

        # Carica dati per ogni giocatore
        players_data = []

        for player_id in player_ids:
            # Trova giocatore in DataFrame
            player_row = self.df_with_overall[self.df_with_overall['Id'] == player_id]

            if player_row.empty:
                # Giocatore non trovato - aggiungi placeholder
                players_data.append(None)
                continue

            player_row = player_row.iloc[0]

            # Estrai dati usando logica esistente
            player_data = self.comparison_logic.extract_player_data(player_row)

            # Calcola prezzo
            price_data = price_calculator.calculate_price_percentage(player_id, budget)
            player_data['price_percentage'] = price_data.get('percentage', 0)
            player_data['price_credits'] = price_data.get('credits', 0)

            players_data.append(player_data)

        # Genera statistiche comparative usando logica esistente
        comparison_stats = self.comparison_logic.compare_players(players_data)

        # Costruisci risposta
        result = {
            'players': [],
            'comparison': comparison_stats,
            'budget': budget
        }

        # Formatta dati giocatori per risposta
        for i, player_data in enumerate(players_data):
            if player_data is None:
                result['players'].append({
                    'id': player_ids[i],
                    'found': False,
                    'nome': 'N/A',
                    'squadra': 'N/A',
                    'ruolo': 'N/A'
                })
            else:
                result['players'].append({
                    'id': int(player_data['Id']),
                    'found': True,
                    'nome': str(player_data['Nome']),
                    'squadra': str(player_data['Squadra']),
                    'ruolo': str(player_data['R']),
                    'fm_weighted': float(player_data['Fm']),
                    'mv_weighted': float(player_data['Mv']),
                    'overall': int(player_data['Overall']) if player_data['Overall'] != 'N/A' else None,
                    'price_percentage': float(player_data['price_percentage']),
                    'price_credits': float(player_data['price_credits']),
                    'seasons_count': int(player_data['seasons_count']),
                    # Role-specific weighted stats
                    'pv_weighted': float(player_data.get('Pv', 0)) if player_data.get('Pv') != 'N/A' else None,
                    'gf_weighted': float(player_data.get('Gf', 0)) if player_data.get('Gf') != 'N/A' else None,
                    'ass_weighted': float(player_data.get('Ass', 0)) if player_data.get('Ass') != 'N/A' else None,
                    'gs_weighted': float(player_data.get('Gs', 0)) if player_data.get('Gs') != 'N/A' else None,
                    'rp_weighted': float(player_data.get('Rp', 0)) if player_data.get('Rp') != 'N/A' else None
                })

        return result
