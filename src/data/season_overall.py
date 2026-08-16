"""
Modulo per il calcolo dell'Overall di una singola stagione
"""
import pandas as pd
import numpy as np
from src.config import ROLE_WEIGHTS
from src.utils.data_utils import extract_base_role


def calculate_single_season_overall(player_stats, role):
    """
    Calcola l'Overall per una singola stagione di un giocatore.
    Usato per confrontare le stagioni e trovare la migliore.

    Args:
        player_stats: Dictionary con le statistiche del giocatore (Pv, Mv, Fm, Gf, Gs, etc.)
        role: Ruolo del giocatore (P, D, C, A)

    Returns:
        Float con l'Overall (0-100) o None se non calcolabile
    """
    base_role = extract_base_role(role)

    if base_role not in ROLE_WEIGHTS:
        return None

    weights = ROLE_WEIGHTS[base_role]
    weighted_sum = 0
    total_weight = 0

    # Per i portieri, calcola Gs per partita
    gs_per_partita = None
    if base_role == 'P' and 'Gs' in player_stats and 'Pv' in player_stats:
        pv = player_stats.get('Pv', 0)
        gs = player_stats.get('Gs', 0)
        if pv > 0:
            gs_per_partita = gs / pv

    for stat, weight in weights.items():
        value = None

        # Per i portieri, usa Gs_per_partita invece di Gs
        if base_role == 'P' and stat == 'Gs':
            value = gs_per_partita
            # Inverti per Gs: meno è meglio, quindi più alto è meglio nel calcolo
            if value is not None:
                value = 100 - (value * 10)  # Normalizza approssimativamente
        else:
            value = player_stats.get(stat)

        if value is not None and pd.notna(value):
            # Normalizza approssimativamente i valori (scala 0-100)
            normalized_value = value

            if stat == 'Mv':
                normalized_value = (value - 5) * 50  # Mv tipicamente tra 5-7
            elif stat == 'Fm':
                normalized_value = (value - 5) * 20  # Fm tipicamente tra 5-10
            elif stat == 'Pv':
                normalized_value = (value / 38) * 100  # Pv max 38
            elif stat in ['Gf', 'Ass']:
                normalized_value = (value / 20) * 100  # Max ~20
            elif stat == 'Rp':
                normalized_value = (value / 10) * 100  # Max ~10

            normalized_value = max(0, min(100, normalized_value))
            weighted_sum += normalized_value * weight
            total_weight += weight

    if total_weight > 0:
        overall = weighted_sum / total_weight
        return round(overall, 1)

    return None
