"""
Configurazione centrale dell'applicazione FantaCalcio
"""
import re

# Percorsi file dati
DATA_DIR = "data"
CURRENT_SEASON_FILE = "CURRENT_SEASON_2026_2027.csv"
STATS_FILES = {
    'recent': ('FM_STATS_202526.csv', 0.60),
    'middle': ('FM_STATS_202425.csv', 0.30),
    'old': ('FM_STATS_202324.csv', 0.10)
}


def extract_season_from_filename(filename):
    """
    Estrae l'anno della stagione dal nome file.

    Args:
        filename: Nome file (es. 'FM_STATS_202526.csv' o 'CURRENT_SEASON_2026_2027.csv')

    Returns:
        Stringa formattata (es. '2025-26' o '2026/2027') o None se non trovata
    """
    # Pattern per file statistiche: FM_STATS_202526.csv → 2025-26
    match = re.search(r'(\d{4})(\d{2})\.csv', filename)
    if match:
        year1 = match.group(1)
        year2 = match.group(2)
        return f"{year1}-{year2}"

    # Pattern per stagione corrente: CURRENT_SEASON_2026_2027.csv → 2026/2027
    match = re.search(r'(\d{4})_(\d{4})\.csv', filename)
    if match:
        year1 = match.group(1)
        year2 = match.group(2)
        return f"{year1}/{year2}"

    return None


def get_season_labels():
    """
    Genera automaticamente le label delle stagioni dai file configurati.

    Returns:
        Dictionary con chiavi 'recent', 'middle', 'old' e valori come '2025-26'
    """
    labels = {}
    for key, (filename, _) in STATS_FILES.items():
        season = extract_season_from_filename(filename)
        if season:
            labels[key] = season
    return labels


def get_current_season_label():
    """
    Ottiene la label della stagione corrente dal file configurato.

    Returns:
        Stringa formattata (es. '2026/2027') o 'N/A' se non trovata
    """
    season = extract_season_from_filename(CURRENT_SEASON_FILE)
    return season if season else 'N/A'


def get_season_names_list():
    """
    Ottiene una lista ordinata dei nomi delle stagioni (dalla più vecchia alla più recente).

    Returns:
        Lista di stringhe (es. ['2023-24', '2024-25', '2025-26'])
    """
    labels = get_season_labels()
    # Ordina per chiave (old, middle, recent)
    order = ['old', 'middle', 'recent']
    return [labels.get(key, 'N/A') for key in order if key in labels]


# Genera automaticamente le label delle stagioni
SEASON_LABELS = get_season_labels()
CURRENT_SEASON_LABEL = get_current_season_label()

# Colonne numeriche da processare
NUMERIC_COLUMNS = ['Pv', 'Mv', 'Fm', 'Gf', 'Gs', 'Rp', 'Rc', 'R+', 'R-', 'Ass', 'Amm', 'Esp', 'Au']

# Pesi per il calcolo Overall (somma = 1.0 per ogni ruolo)
ROLE_WEIGHTS = {
    'P': {  # Portieri
        'Fm': 0.35,
        'Mv': 0.25,
        'Pv': 0.15,
        'Rp': 0.15,
        'Gs': 0.10
    },
    'D': {  # Difensori
        'Fm': 0.30,
        'Mv': 0.25,
        'Pv': 0.15,
        'Gf': 0.18,
        'Ass': 0.12
    },
    'C': {  # Centrocampisti
        'Fm': 0.28,
        'Mv': 0.22,
        'Pv': 0.15,
        'Gf': 0.18,
        'Ass': 0.17
    },
    'A': {  # Attaccanti
        'Gf': 0.40,
        'Ass': 0.22,
        'Fm': 0.18,
        'Mv': 0.12,
        'Pv': 0.08
    }
}

# Soglie per il calcolo dei trend
TREND_THRESHOLD = 0.1

# Soglie presenze per penalità Overall (ridotte per ruoli offensivi)
MIN_PARTITE_AFFIDABILI = 15
PENALTY_THRESHOLDS = [
    (10, 0.60),   # < 10 partite: -40%
    (15, 0.80),   # < 15 partite: -20%
    (25, 0.95),   # < 25 partite: -5%
]

# Penalità specifiche per ruolo (gli attaccanti vengono penalizzati meno)
PENALTY_THRESHOLDS_BY_ROLE = {
    'P': [  # Portieri: penalità più severe (servono continuità)
        (10, 0.50),
        (20, 0.70),
        (28, 0.90),
    ],
    'D': [  # Difensori: penalità moderate
        (10, 0.55),
        (18, 0.75),
        (25, 0.92),
    ],
    'C': [  # Centrocampisti: penalità moderate
        (10, 0.60),
        (15, 0.80),
        (22, 0.93),
    ],
    'A': [  # Attaccanti: penalità ridotte (conta più la resa)
        (8, 0.70),   # < 8 partite: -30%
        (12, 0.85),  # < 12 partite: -15%
        (18, 0.95),  # < 18 partite: -5%
    ]
}

# Budget default per l'asta
DEFAULT_AUCTION_BUDGET = 500

# Pesi per il calcolo del prezzo percentuale
PRICE_WEIGHTS = {
    'overall': 0.4,
    'percentile': 0.3,
    'stats': 0.3
}

# Statistiche chiave per ruolo (per calcolo prezzo)
PRICE_KEY_STATS = {
    'P': ['Fm', 'Mv', 'Rp'],
    'D': ['Fm', 'Mv', 'Gf'],
    'C': ['Fm', 'Gf', 'Ass'],
    'A': ['Gf', 'Ass', 'Fm']
}

# Modificatori trend per calcolo prezzo
TREND_MODIFIERS = {
    '↑': 1.05,  # +5%
    '↓': 0.95,  # -5%
    '→': 1.0    # nessun modificatore
}
