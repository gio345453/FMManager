# Clean Sheet Serie A - Stagione Corrente (dati finali)
# Fonti: AS.com, Sofascore, StatMuse, FBRef
# NOTA: Aggiornare questi dati manualmente quando si cambia stagione in config.py

CLEAN_SHEETS_CURRENT_SEASON = {
    # TOP portieri stagione corrente (dati confermati)
    'Butez': 19,          # Como - MIGLIOR PORTIERE per CS in Serie A!
    'Svilar': 16,         # Roma - Miglior portiere Serie A (premio ufficiale)
    'Carnesecchi': 15,    # Atalanta - Top tier
    'Maignan': 14,        # Milan
    'Sommer': 14,         # Inter (Martinez Jo.)
    'Di Gregorio': 13,    # Juventus
    'Meret': 12,          # Napoli
    'De Gea': 11,         # Fiorentina
    'Provedel': 10,       # Lazio
    'Skorupski': 9,       # Bologna
    'Milinkovic-Savic': 8, # Torino
    'Falcone': 7,         # Lecce
    'Okoye': 7,           # Udinese
    'Montipo': 6,         # Verona
    'Vasquez': 6,         # Genoa
    'Sherri': 5,          # Empoli
    'Scuffet': 5,         # Cagliari
    'Suzuki': 5,          # Parma
    'Audero': 4,          # Como (secondo portiere)
    'Joronen': 3,         # Venezia
    'Stankovic': 2,       # Venezia (poche presenze)
}

# Mapping nomi alternativi
GOALKEEPER_NAME_MAPPING = {
    'Martinez Jo.': 'Sommer',
    'Carnesecchi': 'Carnesecchi',
    'De Gea': 'De Gea',
    'Svilar': 'Svilar',
    'Stankovic F.': 'Stankovic',
    'Di Gregorio': 'Di Gregorio',
    'Maignan': 'Maignan',
    'Meret': 'Meret',
    'Butez': 'Butez'
}

def get_clean_sheets(goalkeeper_name):
    """Ottiene il numero di clean sheet per un portiere nella stagione corrente"""
    # Prova match diretto
    if goalkeeper_name in CLEAN_SHEETS_CURRENT_SEASON:
        return CLEAN_SHEETS_CURRENT_SEASON[goalkeeper_name]

    # Prova mapping alternativo
    mapped_name = GOALKEEPER_NAME_MAPPING.get(goalkeeper_name)
    if mapped_name and mapped_name in CLEAN_SHEETS_CURRENT_SEASON:
        return CLEAN_SHEETS_CURRENT_SEASON[mapped_name]

    # Prova match parziale
    for key, value in CLEAN_SHEETS_CURRENT_SEASON.items():
        if key.lower() in goalkeeper_name.lower() or goalkeeper_name.lower() in key.lower():
            return value

    return 0
