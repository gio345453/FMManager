"""
Optimizer service - wrappa KnapsackOptimizer esistente
NON modifica le formule, usa direttamente la logica esistente
"""
from typing import Dict, List, Any, Optional
from src.logic.knapsack_optimizer import KnapsackOptimizer
from src.data.calculator import StatsCalculator
from src.data.calculators.price_calculator import PriceCalculator


class OptimizerService:
    """Service layer per Build Rosa optimization"""

    def __init__(self, df_with_overall=None):
        """Inizializza service con logica esistente"""
        if df_with_overall is not None:
            # Usa DataFrame già caricato (da PlayerService)
            self.df_with_overall = df_with_overall
        else:
            # Fallback: calcola da zero
            self.calculator = StatsCalculator()
            df = self.calculator.calculate_weighted_stats()
            self.df_with_overall = self.calculator.calculate_overall_scores(df)

    def build_rosa(
        self,
        budget: float,
        composition: Dict[str, int],
        budget_per_role: Dict[str, float],
        selected_players: Optional[Dict[int, Dict]] = None,
        blacklisted_teams: Optional[List[str]] = None,
        custom_credits: Optional[Dict[int, float]] = None,
        value_priority: str = "FM",
        price_percentage: float = 100,
        blacklisted_player_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Costruisce rosa ottimale usando KnapsackOptimizer

        Args:
            budget: Budget totale
            composition: Dict con numero giocatori per ruolo {'P': 3, 'D': 8, 'C': 8, 'A': 6}
            budget_per_role: Budget % per ruolo {'P': 15, 'D': 30, 'C': 30, 'A': 25}
            selected_players: Giocatori già selezionati dall'utente {pos_idx: player_data}
            blacklisted_teams: Lista squadre da escludere
            custom_credits: Crediti custom per posizione {pos_idx: crediti}
            value_priority: Priorità valutazione (FM/MV/PV)
            price_percentage: Percentuale prezzo acquisto (default 100%)
            blacklisted_player_ids: Lista ID giocatori da escludere

        Returns:
            Dict con giocatori selezionati e statistiche rosa
        """
        if selected_players is None:
            selected_players = {}
        if blacklisted_teams is None:
            blacklisted_teams = []
        if custom_credits is None:
            custom_credits = {}
        if blacklisted_player_ids is None:
            blacklisted_player_ids = []

        # Filtra DataFrame escludendo giocatori nella blacklist
        df_filtered = self.df_with_overall.copy()
        if blacklisted_player_ids:
            # Usa 'Id' maiuscolo (come nel DataFrame interno)
            df_filtered = df_filtered[~df_filtered['Id'].isin(blacklisted_player_ids)]

        # Applica price_percentage al DataFrame
        if price_percentage != 100:
            df_filtered = df_filtered.copy()
            df_filtered['quotazione_attuale'] = df_filtered['quotazione_attuale'] * (price_percentage / 100.0)

        print(f"[OptimizerService] Starting optimization:")
        print(f"  - Total players in DB: {len(self.df_with_overall)}")
        print(f"  - After blacklist filter: {len(df_filtered)}")
        print(f"  - Empty positions to fill: {len([i for i in range(sum(composition.values())) if i not in (selected_players or {})])}")
        print(f"  - Budget: {budget}, Price %: {price_percentage}")
        print(f"  - Selected players: {len(selected_players)}")
        print(f"  - Custom credits: {custom_credits}")
        print(f"  - Blacklisted player IDs: {blacklisted_player_ids}")

        # Inizializza PriceCalculator e Optimizer
        price_calculator = PriceCalculator(
            all_players_df=df_filtered,
            use_optimized=True
        )

        # KnapsackOptimizer richiede df, price_calculator, budget
        optimizer = KnapsackOptimizer(
            df=df_filtered,
            price_calculator=price_calculator,
            budget=budget
        )

        # Costruisci mappa posizioni -> ruoli
        position_roles = []
        for role in ['P', 'D', 'C', 'A']:
            for _ in range(composition[role]):
                position_roles.append(role)

        # Trova posizioni vuote (quelle non in selected_players)
        total_positions = sum(composition.values())
        empty_positions = [i for i in range(total_positions) if i not in selected_players]

        # Ottimizza posizioni vuote
        try:
            optimized_players = optimizer.optimize_positions(
                empty_positions=empty_positions,
                position_roles=position_roles,
                budget_per_role=budget_per_role,
                selected_players=selected_players,
                value_priority=value_priority,
                blacklisted_teams=set(blacklisted_teams),
                custom_credits=custom_credits,
                blacklisted_player_ids=blacklisted_player_ids
            )

            print(f"[OptimizerService] Optimization result: {len(optimized_players)} players generated")
        except ValueError as e:
            # Propaga errore con dettagli al frontend
            print(f"[OptimizerService] Optimization failed: {str(e)}")
            raise ValueError(str(e))

        # Combina giocatori manuali + generati
        all_players = {**selected_players, **optimized_players}

        # Costruisci risultato con statistiche
        result_players = []
        total_cost = 0.0
        stats_by_role = {'P': [], 'D': [], 'C': [], 'A': []}

        for pos_idx in range(total_positions):
            role = position_roles[pos_idx]

            if pos_idx in all_players:
                player_data = all_players[pos_idx]
                player_id = player_data.get('id')

                # Trova giocatore in DataFrame
                player_row = self.df_with_overall[self.df_with_overall['Id'] == player_id]

                if not player_row.empty:
                    player_row = player_row.iloc[0]

                    # Calcola prezzo
                    if pos_idx in custom_credits:
                        price = custom_credits[pos_idx]
                    else:
                        price_data = price_calculator.calculate_price_percentage(player_id, budget)
                        price = price_data.get('credits', 0)

                    total_cost += price

                    # Estrai valori puliti
                    fm_weighted_raw = player_row.get('Fm_weighted', 0)
                    if isinstance(fm_weighted_raw, str):
                        # Rimuovi frecce e altri caratteri
                        fm_weighted_clean = fm_weighted_raw.split()[0].replace(',', '.')
                        fm_weighted = float(fm_weighted_clean)
                    else:
                        fm_weighted = float(fm_weighted_raw) if fm_weighted_raw else 0.0

                    player_result = {
                        'position': pos_idx,
                        'id': int(player_id),
                        'nome': str(player_data.get('name', player_row['Nome'])),
                        'ruolo': str(role),
                        'squadra': str(player_data.get('squadra', player_row['Squadra'])),
                        'overall': int(player_row.get('Overall', 0)) if player_row.get('Overall') != 'N/A' else None,
                        'fm_weighted': fm_weighted,
                        'price_credits': float(price),
                        'price_percentage': float((price / budget) * 100),
                        'is_manual': pos_idx in selected_players
                    }

                    result_players.append(player_result)
                    stats_by_role[role].append(player_result)

        # Calcola statistiche aggregate
        stats_aggregate = {}
        for role in ['P', 'D', 'C', 'A']:
            role_players = stats_by_role[role]
            if role_players:
                avg_overall = sum(p['overall'] or 0 for p in role_players) / len(role_players)
                avg_fm = sum(p['fm_weighted'] for p in role_players) / len(role_players)
                total_cost_role = sum(p['price_credits'] for p in role_players)

                stats_aggregate[role] = {
                    'count': len(role_players),
                    'avg_overall': round(avg_overall, 1),
                    'avg_fm': round(avg_fm, 2),
                    'total_cost': round(total_cost_role, 1),
                    'budget_percentage': round((total_cost_role / budget) * 100, 1)
                }
            else:
                stats_aggregate[role] = {
                    'count': 0,
                    'avg_overall': 0.0,
                    'avg_fm': 0.0,
                    'total_cost': 0.0,
                    'budget_percentage': 0.0
                }

        return {
            'success': True,
            'players': result_players,
            'stats': {
                'total_players': len(result_players),
                'budget_used_percentage': round((total_cost / budget) * 100, 1),
                'stats_by_role': stats_aggregate,
                'composition': composition,
                'value_priority': value_priority
            },
            'budget_used': round(total_cost, 1),
            'budget_remaining': round(budget - total_cost, 1)
        }
