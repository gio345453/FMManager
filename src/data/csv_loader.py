"""
Modulo base per il caricamento dei file CSV
"""
import pandas as pd
import os
from src.config import DATA_DIR, NUMERIC_COLUMNS


def load_csv_base(filename):
    """
    Carica un file CSV generico e converte le colonne numeriche

    Args:
        filename: Nome del file da caricare (relativo a DATA_DIR)

    Returns:
        DataFrame pandas o None in caso di errore
    """
    try:
        filepath = os.path.join(DATA_DIR, filename)
        df = pd.read_csv(filepath, sep=';', encoding='utf-8')

        # Converti colonne numeriche (formato italiano con virgola) in un'unica operazione
        if 'Mv' in df.columns or 'Fm' in df.columns:
            cols_to_convert = [col for col in NUMERIC_COLUMNS if col in df.columns]
            for col in cols_to_convert:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        return df
    except Exception as e:
        print(f"Errore nel caricamento di {filename}: {e}")
        return None
