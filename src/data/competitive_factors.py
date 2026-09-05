"""
Estensione formula con percentili interni, fattore competitivo asta e bonus scarsità
RICALIBRATO per target <1% errore
"""

# Fattore competitivo NON lineare - moderato
# Top player crescono ma non eccessivamente
COMPETITIVE_FACTOR = {
    'percentile_95_100': 1.12,  # Top 5% - moderato
    'percentile_90_95': 1.08,   # Top 10%
    'percentile_80_90': 1.04,   # Top 20%
    'percentile_70_80': 1.02,   # Top 30%
    'percentile_0_70': 1.0
}

# Bonus scarsità MODERATO - bilanciato per evitare sovrastima fascia media
SCARCITY_BONUS = {
    'A': {
        'top_stat': 'Gf',
        'thresholds': [
            (15, 1.22),  # Top scorer 15+
            (13, 1.14),  # 13-14 gol
            (11, 1.08),  # 11-12 gol - RIDOTTO per Hojlund
            (9, 1.04),   # 9-10 gol
            (0, 1.0)
        ]
    },
    'C': {
        'top_stat': 'Gf',
        'thresholds': [
            (12, 1.16),  # Ridotto da 1.18
            (10, 1.10),  # Ridotto da 1.12
            (8, 1.06),   # Ridotto da 1.08
            (6, 1.03),   # Ridotto da 1.04
            (0, 1.0)
        ]
    },
    'D': {
        'top_stat': 'Gf',
        'thresholds': [
            (8, 1.18),
            (6, 1.12),
            (5, 1.08),
            (3, 1.04),
            (0, 1.0)
        ]
    },
    'P': {
        'top_stat': 'Rp',
        'thresholds': [
            (3, 1.12),
            (2, 1.08),
            (1, 1.04),
            (0, 1.0)
        ]
    }
}

# NUOVO: Bonus scarsità per FM alto (portieri FM>6 sono rarissimi!)
FM_SCARCITY_BONUS = {
    'P': {
        (6.5, 999): 1.35,  # FM 6.5+ = eccezionale
        (6.3, 6.5): 1.25,  # FM 6.3-6.5 = ottimo
        (6.1, 6.3): 1.15,  # FM 6.1-6.3 = buono
        (5.9, 6.1): 1.05,  # FM 5.9-6.1 = nella media
        (0, 5.9): 1.0
    },
    'D': {
        (6.5, 999): 1.20,
        (6.2, 6.5): 1.12,
        (6.0, 6.2): 1.06,
        (0, 6.0): 1.0
    },
    'C': {
        (7.0, 999): 1.20,
        (6.7, 7.0): 1.12,
        (6.4, 6.7): 1.06,
        (0, 6.4): 1.0
    },
    'A': {
        (7.0, 999): 1.15,
        (6.7, 7.0): 1.08,
        (6.4, 6.7): 1.04,
        (0, 6.4): 1.0
    }
}

def get_fm_scarcity_bonus(fm_value, role):
    """Calcola bonus per FM alto (scarsità)"""
    if role not in FM_SCARCITY_BONUS or fm_value is None:
        return 1.0

    thresholds = FM_SCARCITY_BONUS[role]
    for (min_fm, max_fm), bonus in thresholds.items():
        if min_fm <= fm_value < max_fm:
            return bonus

    return 1.0

