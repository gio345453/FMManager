"""
Modulo per la normalizzazione degli Overall dei portieri
"""


def normalize_goalkeeper_overall(df):
    """
    Normalizza gli Overall dei portieri per renderli comparabili con altri ruoli.
    Trova il massimo Overall tra i portieri e scala a 99.

    Args:
        df: DataFrame con colonna Overall

    Returns:
        DataFrame con Overall dei portieri normalizzati
    """
    # Trova il massimo Overall tra i portieri
    portieri_mask = df['R'].str.startswith('P', na=False)
    portieri_overall = [
        score for score in df[portieri_mask]['Overall']
        if isinstance(score, (int, float)) and score != 'N/A'
    ]

    if portieri_overall:
        max_portiere_overall = max(portieri_overall)
        if max_portiere_overall > 0:
            scaling_factor = 99.0 / max_portiere_overall

            # Applica scaling solo ai portieri
            for idx in df[portieri_mask].index:
                current_overall = df.at[idx, 'Overall']
                if isinstance(current_overall, (int, float)) and current_overall != 'N/A':
                    scaled_overall = int(round(current_overall * scaling_factor))
                    df.at[idx, 'Overall'] = max(1, min(99, scaled_overall))

    return df
