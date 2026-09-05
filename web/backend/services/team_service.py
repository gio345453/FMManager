"""
Team service - wrappa TeamStatsManager esistente
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from src.data.team_stats import TeamStatsManager
from src.data.season_standings import load_previous_season_standings
from src.config import STATS_FILES, CURRENT_SEASON_FILE
from src.data.cache import DataCache


class TeamService:
    """Service layer per operazioni sulle squadre"""

    def __init__(self, players_df=None):
        """Inizializza service"""
        self.team_stats_manager = TeamStatsManager(players_df)

    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Ottieni lista tutte le squadre con statistiche base

        Returns:
            Lista dizionari con dati squadre
        """
        teams = []
        standings = load_previous_season_standings()

        for team_name, data in standings.items():
            teams.append({
                'squadra': team_name,
                'posizione': data['position'],
                'punti': data['points'],
                'gol_fatti': data['gf'],
                'gol_subiti': data['gs'],
                'differenza_reti': data['gf'] - data['gs']
            })

        # Ordina per posizione
        teams.sort(key=lambda x: x['posizione'])

        return teams

    def get_neopromosse(self) -> List[str]:
        """
        Identifica le squadre neopromosse (presenti nella lista giocatori ma senza statistiche)

        Returns:
            Lista nomi squadre neopromosse
        """
        cache = DataCache()

        # Squadre nella lista giocatori (CURRENT_SEASON)
        df_current = cache.get(CURRENT_SEASON_FILE)
        if df_current is None or df_current.empty:
            return []
        all_teams = set(df_current['Squadra'].dropna().unique())

        # Squadre con statistiche (recent)
        recent_file, _ = STATS_FILES.get('recent', (None, None))
        if not recent_file:
            return []
        df_recent = cache.get(recent_file)
        if df_recent is None or df_recent.empty:
            return []
        teams_with_stats = set(df_recent['Squadra'].dropna().unique())

        # Neopromosse = squadre presenti ma senza statistiche
        neopromosse = all_teams - teams_with_stats

        return sorted(list(neopromosse))

    def get_team_stats(self, team_name: str, include_roster: bool = False) -> Optional[Dict[str, Any]]:
        """
        Ottieni statistiche complete per una squadra

        Args:
            team_name: Nome squadra
            include_roster: Se True, include lista completa giocatori (solo stagione corrente)

        Returns:
            Dizionario con statistiche complete o None
        """
        stats = self.team_stats_manager.get_team_stats(team_name)

        if stats is None:
            return None

        # Se richiesto, aggiungi la lista dei giocatori dalla stagione corrente
        if include_roster:
            cache = DataCache()
            df_current = cache.get(CURRENT_SEASON_FILE)

            if df_current is not None and not df_current.empty:
                team_players = df_current[df_current['Squadra'] == team_name]

                if not team_players.empty:
                    # Load stats file to get player statistics
                    from src.config import STATS_FILES
                    stats_key = list(STATS_FILES.keys())[0]  # Most recent season
                    stats_filename = STATS_FILES[stats_key][0]
                    df_stats = cache.get(stats_filename)

                    roster = []
                    for _, player in team_players.iterrows():
                        player_id = int(player['Id'])
                        player_name = str(player['Nome'])
                        player_role = str(player['R'])

                        # Find stats for this player
                        stats_row = None
                        if df_stats is not None and not df_stats.empty:
                            stats_match = df_stats[df_stats['Id'] == player_id]
                            if not stats_match.empty:
                                stats_row = stats_match.iloc[0]

                        # Build roster entry with stats if available
                        roster.append({
                            'id': player_id,
                            'nome': player_name,
                            'ruolo': player_role,
                            'pv': int(stats_row['Pv']) if stats_row is not None and pd.notna(stats_row.get('Pv')) else 0,
                            'fm': float(stats_row['Fm']) if stats_row is not None and pd.notna(stats_row.get('Fm')) else 0.0,
                            'mv': float(stats_row['Mv']) if stats_row is not None and pd.notna(stats_row.get('Mv')) else 0.0,
                            'gf': int(stats_row['Gf']) if stats_row is not None and pd.notna(stats_row.get('Gf')) else 0,
                            'ass': int(stats_row['Ass']) if stats_row is not None and pd.notna(stats_row.get('Ass')) else 0
                        })
                    stats['roster'] = roster
                else:
                    stats['roster'] = []
            else:
                stats['roster'] = []

        return stats

    def get_team_summary(self) -> Dict[str, Any]:
        """
        Ottieni summary tutte le squadre

        Returns:
            Dizionario con summary squadre
        """
        return self.team_stats_manager.get_all_teams_summary()
