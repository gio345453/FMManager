"""
Modulo per il caricamento della stagione corrente
"""
from src.config import CURRENT_SEASON_FILE
from src.data.cache import DataCache


class CurrentSeasonLoader:
    """Gestisce il caricamento dei dati della stagione corrente"""

    def __init__(self):
        self.season_file = CURRENT_SEASON_FILE
        self.cache = DataCache()

    def load_current_season(self):
        """
        Carica i dati della stagione corrente

        Returns:
            DataFrame con i giocatori della stagione corrente o None
        """
        return self.cache.get(self.season_file)

    def extract_player_info(self, player_row):
        """
        Estrae le informazioni base di un giocatore

        Args:
            player_row: Serie pandas con i dati del giocatore

        Returns:
            Dictionary con Id, Nome, Squadra, R (ruolo), RM (ruoli multipli)
        """
        return {
            'Id': player_row['Id'],
            'Nome': player_row['Nome'],
            'Squadra': player_row['Squadra'],
            'R': player_row['R'],
            'RM': str(player_row['RM']).strip()
        }

    def format_role_display(self, base_role, rm_value):
        """
        Formatta la visualizzazione del ruolo con eventuali ruoli multipli

        Args:
            base_role: Ruolo base (P, D, C, A)
            rm_value: Valore del campo RM (ruoli multipli)

        Returns:
            Stringa formattata (es. "C (T;E)" o "P")
        """
        role_display = base_role
        roles_to_show = []

        if rm_value and rm_value != 'nan':
            rm_parts = rm_value.split(';')
            for part in rm_parts:
                part = part.strip().strip('"')
                if part in ['T', 'E']:
                    roles_to_show.append(part)

        if roles_to_show:
            role_display = f"{base_role} ({';'.join(roles_to_show)})"

        return role_display
