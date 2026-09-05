"""
Utilities per manipolazione dati giocatori - Funzioni consolidate
"""
import pandas as pd


def clean_numeric_value(value):
    """
    Pulisce e converte un valore numerico rimuovendo simboli trend.

    Rimuove i simboli: ↑, ↓, → e converte il risultato in float.
    Gestisce None, NaN, int, float e stringhe.

    Args:
        value: Valore da convertire (può contenere ↑, ↓, →)

    Returns:
        float o None se non convertibile

    Examples:
        >>> clean_numeric_value("7.5 ↑")
        7.5
        >>> clean_numeric_value(10)
        10.0
        >>> clean_numeric_value("N/A")
        None
    """
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    # Rimuovi simboli trend
    str_val = str(value).replace('↑', '').replace('↓', '').replace('→', '').strip()

    try:
        return float(str_val)
    except (ValueError, TypeError):
        return None


def extract_base_role(role_string):
    """
    Estrae il ruolo base (P, D, C, A) da una stringa che può contenere ruoli multipli.

    Args:
        role_string: Stringa ruolo (es. "D", "C (T)", "A", "D (T;E)")

    Returns:
        Carattere del ruolo base (P, D, C, A). Default: 'C'

    Examples:
        >>> extract_base_role("D (T;E)")
        'D'
        >>> extract_base_role("P")
        'P'
        >>> extract_base_role(None)
        'C'
    """
    if not role_string:
        return 'C'  # Default centrocampista

    # Prendi solo il primo carattere prima di eventuali parentesi
    base = str(role_string).split('(')[0].strip()
    if base:
        return base[0].upper()

    return 'C'


def extract_value_and_trend(raw_value):
    """
    Separa il valore numerico dal simbolo di trend.

    Args:
        raw_value: Valore grezzo (es. "7.5 ↑", "8.2", "N/A")

    Returns:
        tuple (numeric_value: float, trend_symbol: str)
        Il valore numerico è sempre un float (0.0 se non valido)

    Examples:
        >>> extract_value_and_trend("7.5 ↑")
        (7.5, '↑')
        >>> extract_value_and_trend("8.2")
        (8.2, '')
        >>> extract_value_and_trend("N/A")
        (0.0, '')
    """
    if pd.isna(raw_value):
        return 0.0, ''

    str_val = str(raw_value)

    # Cerca simbolo trend
    trend = ''
    if '↑' in str_val:
        trend = '↑'
    elif '↓' in str_val:
        trend = '↓'
    elif '→' in str_val:
        trend = '→'

    # Estrai valore numerico
    numeric = clean_numeric_value(raw_value)

    return numeric if numeric is not None else 0.0, trend


def extract_values_and_trends_batch(series):
    """
    Estrae valori e trend da una Series pandas in batch (operazione vettoriale).

    Questa funzione è MOLTO più veloce di chiamare extract_value_and_trend()
    in un loop, perché usa operazioni vettoriali di pandas.

    Args:
        series: pandas Series con valori (es. "7.5 ↑", "8.2", "N/A")

    Returns:
        DataFrame con colonne 'value' (float) e 'trend' (str)

    Examples:
        >>> s = pd.Series(["7.5 ↑", "8.2", "N/A", "6.0 ↓"])
        >>> extract_values_and_trends_batch(s)
           value trend
        0    7.5     ↑
        1    8.2
        2    0.0
        3    6.0     ↓
    """
    if series is None or series.empty:
        return pd.DataFrame({'value': [], 'trend': []})

    # Converti a stringhe gestendo NaN
    str_series = series.fillna('0').astype(str)

    # Estrai simboli trend con regex (operazione vettoriale)
    trends = str_series.str.extract(r'(↑|↓|→)', expand=False).fillna('')

    # Rimuovi trend e converti a float (operazione vettoriale)
    clean_values = str_series.str.replace(r'[↑↓→]', '', regex=True).str.strip()
    values = pd.to_numeric(clean_values, errors='coerce').fillna(0.0)

    return pd.DataFrame({'value': values.values, 'trend': trends.values}, index=series.index)


def format_stat_display(value, decimals=2, show_na=True):
    """
    Formatta una statistica per la visualizzazione preservando i trend.

    Args:
        value: Valore da formattare (numero, stringa con trend, None, N/A)
        decimals: Numero di decimali (default 2)
        show_na: Se True mostra "N/A" per valori None, altrimenti "-"

    Returns:
        str: Valore formattato per display

    Examples:
        >>> format_stat_display("7.50 ↑")
        "7.50 ↑"
        >>> format_stat_display(8.123456, decimals=1)
        "8.1"
        >>> format_stat_display(None)
        "N/A"
    """
    if pd.isna(value) or value is None:
        return "N/A" if show_na else "-"

    # Se è già una stringa con trend, preservala
    if isinstance(value, str):
        numeric, trend = extract_value_and_trend(value)
        if numeric is None:
            return "N/A" if show_na else "-"
        formatted = f"{numeric:.{decimals}f}"
        return f"{formatted} {trend}".strip() if trend else formatted

    # Altrimenti formatta come numero
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}"

    return str(value)


def safe_int(value, default=0):
    """
    Conversione sicura a int con gestione errori.

    Args:
        value: Valore da convertire
        default: Valore di default in caso di errore (default 0)

    Returns:
        int: Valore convertito o default

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("invalid", default=1)
        1
        >>> safe_int(None, default=0)
        0
    """
    if pd.isna(value) or value is None:
        return default

    try:
        # Se è una stringa con simboli trend, puliscila prima
        cleaned = clean_numeric_value(value)
        if cleaned is None:
            return default
        return int(cleaned)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """
    Conversione sicura a float con gestione errori.

    Args:
        value: Valore da convertire
        default: Valore di default in caso di errore (default 0.0)

    Returns:
        float: Valore convertito o default

    Examples:
        >>> safe_float("7.5 ↑")
        7.5
        >>> safe_float("invalid", default=1.0)
        1.0
        >>> safe_float(None, default=0.0)
        0.0
    """
    if pd.isna(value) or value is None:
        return default

    cleaned = clean_numeric_value(value)
    if cleaned is None:
        return default

    return cleaned
