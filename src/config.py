"""
Configurazione centrale dell'applicazione FantaCalcio
"""
import re
import os
from datetime import date
from pathlib import Path

# Percorsi file dati - usa path assoluto dalla root del progetto
_ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = os.path.join(_ROOT_DIR, "data")
STATS_DIR = os.path.join(DATA_DIR, "stats")
CONFIG_DIR = os.path.join(DATA_DIR, "config")
USER_DATA_DIR = os.path.join(DATA_DIR, "user_data")
CURRENT_SEASON_FILE = os.path.join("stats", "CURRENT_SEASON_2026_2027.csv")
STATS_FILES = {
    'recent': (os.path.join("stats", "FM_STATS_202526.csv"), 0.60),
    'middle': (os.path.join("stats", "FM_STATS_202425.csv"), 0.30),
    'old': (os.path.join("stats", "FM_STATS_202324.csv"), 0.10)
}

# ============================================================================
# DEFENSE MODIFIER - Bonus difesa configurabile
# ============================================================================
DEFENSE_MODIFIER_ENABLED = True
DEFENSE_MODIFIER_TIERS = [
    (6.0, 1),   # Media >= 6.0 → +1 bonus per giornata
    (6.5, 2),   # Media >= 6.5 → +2 bonus per giornata
    (7.0, 3),   # Media >= 7.0 → +3 bonus per giornata
]

# Impatto sul prezzo (moltiplicatori)
DEFENSE_PRICE_IMPACT = {
    'P': {  # Portieri
        'high': (6.5, 1.15),    # MV >= 6.5 e pochi gol subiti → +15%
        'medium': (6.3, 1.10),  # MV >= 6.3 → +10%
        'low': (6.0, 1.05),     # MV >= 6.0 → +5%
    },
    'D': {  # Difensori
        'high': (6.8, 1.12),    # MV >= 6.8 → +12%
        'medium': (6.5, 1.08),  # MV >= 6.5 → +8%
        'low': (6.3, 1.05),     # MV >= 6.3 → +5%
    }
}

# Impatto sull'Overall (punti aggiuntivi)
DEFENSE_OVERALL_IMPACT = {
    'P': {  # Portieri
        'high': (6.5, 3),    # MV >= 6.5 → +3 overall
        'medium': (6.3, 2),  # MV >= 6.3 → +2 overall
        'low': (6.0, 1),     # MV >= 6.0 → +1 overall
    },
    'D': {  # Difensori
        'high': (6.8, 3),    # MV >= 6.8 → +3 overall
        'medium': (6.5, 2),  # MV >= 6.5 → +2 overall
        'low': (6.3, 1),     # MV >= 6.3 → +1 overall
    }
}
# ============================================================================

# ============================================================================
# FIXTURE DIFFICULTY - Giornata corrente
# ============================================================================
CURRENT_MATCHDAY = 1  # Giornata corrente (1-38), modificabile da UI
# ============================================================================


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


# ============================================================================
# SEASON RESOLUTION - Risoluzione automatica stagioni
# ============================================================================

def format_season(year_start: int) -> str:
    """
    Formatta una stagione come 'YYYY-YY'.

    Args:
        year_start: anno di inizio (es. 2025)

    Returns:
        str: stagione formattata (es. '2025-26')
    """
    year_end = year_start + 1
    return f"{year_start}-{str(year_end)[-2:]}"


def parse_season(season_label: str) -> int | None:
    """
    Estrae l'anno di inizio da una label stagione.

    Args:
        season_label: stringa come '2025-26' o '2025/2026'

    Returns:
        int: anno inizio (es. 2025) o None se non parsabile
    """
    match = re.match(r'^(\d{4})[-/]', season_label)
    return int(match.group(1)) if match else None


def get_current_season(reference_date: date | None = None) -> str:
    """
    Determina la stagione corrente in base alla data.

    La stagione cambia a luglio: fino a fine giugno usa la stagione precedente,
    da luglio in poi usa quella nuova.

    Args:
        reference_date: data di riferimento (default: oggi)

    Returns:
        str: stagione formattata (es. '2026-27')

    Examples:
        >>> get_current_season(date(2026, 6, 30))
        '2025-26'
        >>> get_current_season(date(2026, 7, 1))
        '2026-27'
        >>> get_current_season(date(2026, 8, 29))
        '2026-27'
    """
    today = reference_date or date.today()
    year = today.year
    # Da luglio in poi, la nuova stagione è iniziata
    if today.month >= 7:
        return format_season(year)
    # Prima di luglio, siamo ancora nella stagione precedente
    return format_season(year - 1)


def get_last_completed_season(reference_date: date | None = None) -> str:
    """
    Determina l'ultima stagione Serie A conclusa.

    La stagione si conclude a fine giugno. L'ultima conclusa è quella
    che ha terminato il suo campionato:
    - A giugno 2026: la 2025-26 è ancora in corso → ultima conclusa è 2024-25
    - Da luglio 2026: la 2025-26 è conclusa → ultima conclusa è 2025-26
    - A giugno 2027: la 2026-27 è ancora in corso → ultima conclusa è 2025-26
    - Da luglio 2027: la 2026-27 è conclusa → ultima conclusa è 2026-27

    Args:
        reference_date: data di riferimento (default: oggi)

    Returns:
        str: stagione formattata (es. '2025-26')

    Examples:
        >>> get_last_completed_season(date(2026, 6, 30))
        '2024-25'
        >>> get_last_completed_season(date(2026, 7, 1))
        '2025-26'
        >>> get_last_completed_season(date(2026, 8, 29))
        '2025-26'
        >>> get_last_completed_season(date(2027, 1, 15))
        '2025-26'
        >>> get_last_completed_season(date(2027, 6, 30))
        '2025-26'
        >>> get_last_completed_season(date(2027, 7, 1))
        '2026-27'
    """
    today = reference_date or date.today()
    year = today.year
    # Da luglio in poi: la stagione che inizia (year-1) è conclusa
    if today.month >= 7:
        return format_season(year - 1)
    # Prima di luglio: la stagione che inizia (year-2) è l'ultima conclusa
    return format_season(year - 2)


def get_historical_seasons(count: int = 3, reference_date: date | None = None) -> list[str]:
    """
    Restituisce le ultime N stagioni concluse in ordine decrescente.

    Args:
        count: numero di stagioni da restituire
        reference_date: data di riferimento (default: oggi)

    Returns:
        list: stagioni ordinate dalla più recente (es. ['2025-26', '2024-25', '2023-24'])
    """
    last_completed = get_last_completed_season(reference_date)
    last_year = parse_season(last_completed)
    if last_year is None:
        return []

    return [format_season(last_year - i) for i in range(count)]


def find_current_season_file(stats_dir: str | Path = STATS_DIR) -> Path | None:
    """
    Trova dinamicamente il file CURRENT_SEASON più recente nella directory stats.

    Args:
        stats_dir: directory dove cercare i file

    Returns:
        Path assoluto del file trovato, o None se non esiste
    """
    stats_path = Path(stats_dir)
    if not stats_path.exists():
        return None

    current_season = get_current_season()

    # Cerca file che matchano il pattern CURRENT_SEASON_YYYY_YYYY.csv
    candidates = list(stats_path.glob('CURRENT_SEASON_*.csv'))

    if not candidates:
        return None

    # Preferisci il file della stagione corrente se esiste
    for candidate in candidates:
        if current_season.replace('-', '_') in candidate.name:
            return candidate.resolve()

    # Altrimenti prendi il più recente per nome
    return sorted(candidates, reverse=True)[0].resolve()


def find_stats_files(stats_dir: str | Path = STATS_DIR) -> dict[str, tuple[Path, float]]:
    """
    Trova dinamicamente i file FM_STATS delle ultime 3 stagioni concluse.

    Args:
        stats_dir: directory dove cercare i file

    Returns:
        dict: {'recent': (Path, peso), 'middle': (Path, peso), 'old': (Path, peso)}
    """
    stats_path = Path(stats_dir)
    if not stats_path.exists():
        return {}

    historical = get_historical_seasons(3)
    weights = [0.60, 0.30, 0.10]
    keys = ['recent', 'middle', 'old']

    result = {}
    for key, season, weight in zip(keys, historical, weights):
        # Converte '2025-26' → '202526'
        season_compact = season.replace('-', '')
        pattern = f'FM_STATS_{season_compact}.csv'

        file_path = stats_path / pattern
        if file_path.exists():
            result[key] = (file_path.resolve(), weight)

    return result


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
