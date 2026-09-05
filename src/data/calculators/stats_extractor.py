"""
Modulo per l'estrazione e normalizzazione delle statistiche dei giocatori
"""
import pandas as pd
from src.data.clean_sheets_data import get_clean_sheets
from src.utils.data_utils import clean_numeric_value, extract_base_role


class StatsExtractor:
    """Estrae e normalizza le statistiche dai dati dei giocatori"""

    @staticmethod
    def extract_number(value):
        """
        Estrae numero da un valore rimuovendo simboli trend

        Args:
            value: Valore da convertire (può contenere ↑, ↓, →)

        Returns:
            float o None se non convertibile
        """
        return clean_numeric_value(value)

    @staticmethod
    def get_numeric_stat(player_row, stat, role):
        """
        Estrae valore numerico di una statistica con logica speciale per alcuni casi

        Args:
            player_row: Serie pandas con i dati del giocatore
            stat: Nome della statistica da estrarre
            role: Ruolo del giocatore (P, D, C, A)

        Returns:
            float con il valore della statistica o None
        """
        # Caso speciale: Gol subiti per partita
        if stat == 'Gs_per_match':
            gs = StatsExtractor.extract_number(player_row.get('Gs_weighted', 0))
            pv = StatsExtractor.extract_number(player_row.get('Pv_weighted', 1))
            if pv is not None and pv > 0:
                return gs / pv
            return 0

        # Caso speciale: Clean sheets per portieri
        if stat == 'CleanSheets' and role == 'P':
            player_name = player_row.get('Nome', '')
            return get_clean_sheets(player_name)

        # Caso speciale: Gol attaccanti - usa boost per trend recente
        # I gol recenti valgono di più per l'asta
        if stat == 'Gf' and role == 'A' and 'Pv_recent' in player_row.index:
            pv_recent = StatsExtractor.extract_number(player_row.get('Pv_recent', 0))

            # Se ha giocato abbastanza nella stagione recente (15+ partite)
            if pv_recent is not None and pv_recent > 15:
                base_gf = StatsExtractor.extract_number(player_row.get(f'{stat}_weighted', 0))

                # Boost del 30% per attaccanti con trend positivo
                if '↑' in str(player_row.get('Gf_weighted', '')):
                    return base_gf * 1.30

                return base_gf

        # Caso standard: usa il valore ponderato
        col_name = f'{stat}_weighted'
        if col_name not in player_row.index:
            return None

        return StatsExtractor.extract_number(player_row[col_name])

    @staticmethod
    def normalize_stat_value(stat, value, role):
        """
        Normalizza il valore di una statistica (attualmente passa through)

        Args:
            stat: Nome della statistica
            value: Valore da normalizzare
            role: Ruolo del giocatore

        Returns:
            Valore normalizzato (attualmente il valore grezzo)
        """
        # Restituisci il valore grezzo - i pesi lo gestiranno
        return value

    @staticmethod
    def extract_base_role(role_string):
        """
        Estrae il ruolo base da una stringa che può contenere ruoli multipli

        Args:
            role_string: Stringa ruolo (es. "D", "C (T)", "A")

        Returns:
            Carattere del ruolo base (P, D, C, A)
        """
        return extract_base_role(role_string)
