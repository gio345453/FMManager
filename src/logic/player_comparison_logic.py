"""
Logica di confronto giocatori
Gestisce calcoli, comparazioni e analisi tra giocatori
"""

import pandas as pd
import re


class PlayerComparisonLogic:
    """Classe per gestire la logica di confronto tra giocatori"""

    @staticmethod
    def clean_numeric_value(value):
        """Pulisce un valore numerico da simboli e frecce

        Args:
            value: valore da pulire (può essere str, float, o altro)

        Returns:
            float: valore pulito convertito a float, o 0.0 se conversione fallisce
        """
        try:
            if isinstance(value, str):
                # Rimuovi frecce e simboli (↓, ↑, →, ←, spazi)
                value = re.sub(r'[↓↑→←\s]', '', value)
            return float(value) if pd.notna(value) and value != '' else 0.0
        except:
            return 0.0

    @staticmethod
    def extract_player_data(player_row):
        """Estrae e pulisce i dati di un giocatore dal DataFrame

        Args:
            player_row: riga del DataFrame con i dati del giocatore

        Returns:
            dict: dizionario con i dati puliti del giocatore
        """
        fm_val = PlayerComparisonLogic.clean_numeric_value(player_row.get('Fm_weighted', 0))
        mv_val = PlayerComparisonLogic.clean_numeric_value(player_row.get('Mv_weighted', 0))

        return {
            'Id': player_row.get('Id', ''),
            'Nome': player_row.get('Nome', ''),
            'Squadra': player_row.get('Squadra', ''),
            'R': player_row.get('R', ''),
            'Fm': fm_val,
            'Mv': mv_val,
            'Overall': player_row.get('Overall', 0),
            'price_percentage': player_row.get('price_percentage', 0),
            'seasons_count': player_row.get('seasons_count', 1)
        }

    @staticmethod
    def compare_players(players_list):
        """Confronta una lista di giocatori e genera statistiche comparative

        Args:
            players_list: lista di dizionari con dati giocatori

        Returns:
            dict: statistiche comparative (media FM, MV, miglior giocatore, ecc.)
        """
        if not players_list:
            return {}

        # Filtra giocatori validi (con dati non None)
        valid_players = [p for p in players_list if p is not None]

        if not valid_players:
            return {}

        # Calcola medie
        fm_values = [p['Fm'] for p in valid_players if p['Fm'] > 0]
        mv_values = [p['Mv'] for p in valid_players if p['Mv'] > 0]

        avg_fm = sum(fm_values) / len(fm_values) if fm_values else 0
        avg_mv = sum(mv_values) / len(mv_values) if mv_values else 0

        # Trova miglior giocatore per FM
        best_fm_player = max(valid_players, key=lambda p: p['Fm']) if valid_players else None
        best_mv_player = max(valid_players, key=lambda p: p['Mv']) if valid_players else None

        return {
            'count': len(valid_players),
            'avg_fm': avg_fm,
            'avg_mv': avg_mv,
            'best_fm': best_fm_player,
            'best_mv': best_mv_player,
            'fm_values': fm_values,
            'mv_values': mv_values
        }

    @staticmethod
    def format_stat_value(value):
        """Formatta un valore statistico per la visualizzazione

        Args:
            value: valore numerico da formattare

        Returns:
            str: valore formattato (es. "6.45" o "N/A")
        """
        if value and value > 0:
            return f"{value:.2f}"
        return "N/A"

    @staticmethod
    def get_comparison_summary(players_list):
        """Genera un sommario testuale del confronto

        Args:
            players_list: lista di dizionari con dati giocatori

        Returns:
            str: sommario del confronto in formato testuale
        """
        stats = PlayerComparisonLogic.compare_players(players_list)

        if not stats:
            return "Nessun giocatore selezionato"

        summary_lines = [
            f"Giocatori confrontati: {stats['count']}",
            f"FM media: {PlayerComparisonLogic.format_stat_value(stats['avg_fm'])}",
            f"MV media: {PlayerComparisonLogic.format_stat_value(stats['avg_mv'])}"
        ]

        if stats['best_fm']:
            summary_lines.append(f"Miglior FM: {stats['best_fm']['Nome']} ({PlayerComparisonLogic.format_stat_value(stats['best_fm']['Fm'])})")

        if stats['best_mv']:
            summary_lines.append(f"Miglior MV: {stats['best_mv']['Nome']} ({PlayerComparisonLogic.format_stat_value(stats['best_mv']['Mv'])})")

        return "\n".join(summary_lines)
