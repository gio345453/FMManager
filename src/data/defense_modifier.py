"""
Defense Modifier - Calcola l'impatto del bonus difesa su prezzi e overall

Il Defense Modifier è un bonus che premia le difese solide:
- Calcola la media di: portiere + migliori 3 difensori
- Assegna bonus in base a tier configurabili
- Impatta su: prezzo, overall, raccomandazioni, ottimizzatore
"""
from src.config import (
    DEFENSE_MODIFIER_ENABLED,
    DEFENSE_PRICE_IMPACT,
    DEFENSE_OVERALL_IMPACT,
    DEFENSE_MODIFIER_TIERS
)


def calculate_defense_contribution_price(player_data, role):
    """
    Calcola il moltiplicatore di prezzo dovuto al defense modifier

    Args:
        player_data: Dizionario con dati giocatore (mv_weighted, gs_weighted, pv_weighted)
        role: Ruolo giocatore (P/D/C/A)

    Returns:
        float: Moltiplicatore prezzo (1.0 = nessun impatto, 1.15 = +15%)
    """
    if not DEFENSE_MODIFIER_ENABLED:
        return 1.0

    if role not in ['P', 'D']:
        return 1.0

    mv = player_data.get('mv_weighted', 0)
    if mv is None or mv == 0:
        return 1.0

    # Portiere: considera anche gol subiti
    if role == 'P':
        gs = player_data.get('gs_weighted', 0) or 0
        pv = player_data.get('pv_weighted', 1) or 1
        gs_per_partita = gs / max(pv, 1)

        tiers = DEFENSE_PRICE_IMPACT['P']

        # Portiere top: MV alto + pochi gol subiti
        if mv >= tiers['high'][0] and gs_per_partita < 0.9:
            return tiers['high'][1]
        elif mv >= tiers['medium'][0]:
            return tiers['medium'][1]
        elif mv >= tiers['low'][0]:
            return tiers['low'][1]
        else:
            return 1.0

    # Difensore: solo media voto
    elif role == 'D':
        tiers = DEFENSE_PRICE_IMPACT['D']

        if mv >= tiers['high'][0]:
            return tiers['high'][1]
        elif mv >= tiers['medium'][0]:
            return tiers['medium'][1]
        elif mv >= tiers['low'][0]:
            return tiers['low'][1]
        else:
            return 1.0

    return 1.0


def calculate_defense_contribution_overall(player_data, role):
    """
    Calcola i punti overall bonus dovuti al defense modifier

    Args:
        player_data: Dizionario con dati giocatore (mv_weighted)
        role: Ruolo giocatore (P/D/C/A)

    Returns:
        int: Punti da aggiungere all'overall (0-3)
    """
    if not DEFENSE_MODIFIER_ENABLED:
        return 0

    if role not in ['P', 'D']:
        return 0

    mv = player_data.get('mv_weighted', 0)
    if mv is None or mv == 0:
        return 0

    tiers = DEFENSE_OVERALL_IMPACT[role]

    if mv >= tiers['high'][0]:
        return tiers['high'][1]
    elif mv >= tiers['medium'][0]:
        return tiers['medium'][1]
    elif mv >= tiers['low'][0]:
        return tiers['low'][1]
    else:
        return 0


def get_defense_quality_label(player_data, role):
    """
    Restituisce un'etichetta qualitativa per il contributo difensivo

    Args:
        player_data: Dizionario con dati giocatore
        role: Ruolo giocatore (P/D/C/A)

    Returns:
        str: Etichetta ('Ottimo', 'Buono', 'Sufficiente', None)
    """
    if not DEFENSE_MODIFIER_ENABLED:
        return None

    if role not in ['P', 'D']:
        return None

    mv = player_data.get('mv_weighted', 0)
    if mv is None or mv == 0:
        return None

    tiers = DEFENSE_OVERALL_IMPACT[role]

    if mv >= tiers['high'][0]:
        return 'Ottimo'
    elif mv >= tiers['medium'][0]:
        return 'Buono'
    elif mv >= tiers['low'][0]:
        return 'Sufficiente'
    else:
        return None


def estimate_seasonal_defense_bonus(player_data, role, matchdays=36):
    """
    Stima il bonus difesa totale che un giocatore può generare in una stagione

    Args:
        player_data: Dizionario con dati giocatore
        role: Ruolo giocatore (P/D/C/A)
        matchdays: Numero di giornate (default 36)

    Returns:
        dict: {'bonus_per_giornata': float, 'bonus_totale': float, 'descrizione': str}
    """
    if not DEFENSE_MODIFIER_ENABLED or role not in ['P', 'D']:
        return {'bonus_per_giornata': 0, 'bonus_totale': 0, 'descrizione': 'N/A'}

    mv = player_data.get('mv_weighted', 0)
    if mv is None or mv == 0:
        return {'bonus_per_giornata': 0, 'bonus_totale': 0, 'descrizione': 'Dati insufficienti'}

    # Stima conservativa: assume di essere nella formazione titolare
    # e che gli altri 3 difensori/portiere abbiano media simile

    # Trova in che tier rientra questo giocatore
    bonus_per_giornata = 0
    for threshold, bonus in reversed(DEFENSE_MODIFIER_TIERS):
        if mv >= threshold:
            bonus_per_giornata = bonus
            break

    # Considera che non tutte le giornate avrà il bonus (70% realistico)
    bonus_effettivo = bonus_per_giornata * 0.7
    bonus_totale = bonus_effettivo * matchdays

    descrizione = f"~{bonus_effettivo:.1f} bonus/giornata"

    return {
        'bonus_per_giornata': bonus_effettivo,
        'bonus_totale': bonus_totale,
        'descrizione': descrizione
    }


def calculate_defense_lineup_bonus(portiere_mv, difensori_mv):
    """
    Calcola il bonus difesa per una formazione specifica
    (Utile per simulazioni o preview formazione)

    Args:
        portiere_mv: Media voto portiere (float)
        difensori_mv: Lista di medie voto difensori (list[float])

    Returns:
        int: Bonus difesa (0-3+)
    """
    if not DEFENSE_MODIFIER_ENABLED:
        return 0

    if portiere_mv is None or len(difensori_mv) < 4:
        return 0

    # Prendi i 3 migliori difensori
    top_3_difensori = sorted(difensori_mv, reverse=True)[:3]

    # Calcola media
    media_difesa = (portiere_mv + sum(top_3_difensori)) / 4

    # Trova bonus corrispondente
    bonus = 0
    for threshold, value in reversed(DEFENSE_MODIFIER_TIERS):
        if media_difesa >= threshold:
            bonus = value
            break

    return bonus
