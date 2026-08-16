"""
Modulo per il caricamento delle statistiche storiche (stagioni precedenti)
"""
from src.config import STATS_FILES
from src.data.cache import DataCache


class StatsLoader:
    """Gestisce il caricamento delle statistiche storiche"""

    def __init__(self):
        self.stats_files = STATS_FILES
        self.cache = DataCache()

    def load_all_stats(self):
        """
        Carica tutte le stagioni storiche con i loro pesi

        Returns:
            Dictionary con struttura:
            {
                'recent': {'df': DataFrame, 'weight': 0.60},
                'middle': {'df': DataFrame, 'weight': 0.30},
                'old': {'df': DataFrame, 'weight': 0.10}
            }
        """
        stats_data = {}

        for season_key, (filename, weight) in self.stats_files.items():
            df = self.cache.get(filename)
            if df is not None:
                # Imposta Id come indice per lookup veloce
                df_indexed = df.set_index('Id')
                stats_data[season_key] = {'df': df_indexed, 'weight': weight}

        return stats_data

    def get_player_stats(self, player_id, stats_data):
        """
        Recupera le statistiche di un giocatore da tutte le stagioni

        Args:
            player_id: ID del giocatore
            stats_data: Dictionary ritornato da load_all_stats()

        Returns:
            Tuple (seasons_found, recent_stats, middle_stats, season_data)
        """
        seasons_found = 0
        recent_stats = {}
        middle_stats = {}
        season_data = {}

        for season_key, season_info in stats_data.items():
            season_df = season_info['df']

            if player_id in season_df.index:
                seasons_found += 1
                player_row = season_df.loc[player_id]
                season_data[season_key] = player_row

                if season_key == 'recent':
                    recent_stats = player_row.to_dict()
                elif season_key == 'middle':
                    middle_stats = player_row.to_dict()

        return seasons_found, recent_stats, middle_stats, season_data
