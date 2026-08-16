"""
Formula ricalibrата per calcolo percentuale prezzo basata su:
1. Budget totale distribuito: P=11%, D=17.5%, C=31.5%, A=40%
2. Numero giocatori: P=3, D=8, C=8, A=6
3. Forza squadra come moltiplicatore
4. Presenze come fattore critico ma non bloccante
"""

# Budget medio per giocatore per ruolo (su 100%)
ROLE_BUDGET_DISTRIBUTION = {
    'P': {
        'total_budget': 11,  # 11% del budget totale
        'num_players': 3,
        'avg_per_player': 3.67,  # 11/3
        'range': (1, 11)  # min-max %
    },
    'D': {
        'total_budget': 17.5,  # 17.5% del budget totale
        'num_players': 8,
        'avg_per_player': 2.19,  # 17.5/8
        'range': (1, 16)  # min-max %
    },
    'C': {
        'total_budget': 31.5,  # 31.5% del budget totale
        'num_players': 8,
        'avg_per_player': 3.94,  # 31.5/8
        'range': (2, 17)  # min-max %
    },
    'A': {
        'total_budget': 40,  # 40% del budget totale
        'num_players': 6,
        'avg_per_player': 6.67,  # 40/6
        'range': (5, 22)  # min-max %
    }
}

# Coefficienti squadra (da classifiche ponderate)
TEAM_COEFFICIENTS = {
    'Inter': 1.20,
    'Napoli': 1.10,
    'Milan': 1.08,
    'Juventus': 1.05,
    'Atalanta': 1.03,
    'Roma': 0.98,
    'Lazio': 0.95,
    'Fiorentina': 0.93,
    'Bologna': 0.90,
    'Torino': 0.85,
    'Udinese': 0.83,
    'Verona': 0.80,
    'Genoa': 0.78,
    'Cagliari': 0.75,
    'Parma': 0.73,
    'Como': 0.72,
    'Lecce': 0.70,
    'Monza': 0.70,
    'Venezia': 0.68,
    'Empoli': 0.68,
    'Sassuolo': 0.68,
    'Cremonese': 0.65,
    'Pisa': 0.63
}

# Pesi per statistica - OTTIMIZZATO v3 con focus su ranking e titolarità
ROLE_STAT_WEIGHTS = {
    'P': {
        'Pv': 0.025,
        'Fm': 0.40,
        'Gs_per_match': -0.35,
        'Rp': 0.20,
        'CleanSheets': 0.38
    },
    'D': {
        'Pv': 0.015,
        'Fm': 0.20,
        'Gf': 0.50,
        'Ass': 0.08,
        'Amm': -0.12
    },
    'C': {
        'Pv': 0.015,
        'Fm': 0.18,
        'Gf': 0.42,
        'Ass': 0.16,
        'Rc': 0.10
    },
    'A': {
        'Gf': 0.70,
        'Ass': 0.12,
        'Fm': 0.07,
        'Pv': 0.015,
        'Rc': 0.04
    }
}

# Coefficienti squadra - BILANCIATI per matching esperienza utente
TEAM_COEFFICIENTS = {
    'Inter': 1.10,
    'Napoli': 0.95,
    'Milan': 1.05,
    'Juventus': 1.03,
    'Atalanta': 0.95,
    'Roma': 1.08,
    'Lazio': 0.95,
    'Fiorentina': 0.82,
    'Bologna': 0.85,
    'Torino': 0.90,
    'Udinese': 0.83,
    'Verona': 0.80,
    'Genoa': 0.78,
    'Cagliari': 0.76,
    'Parma': 0.73,
    'Como': 0.80,
    'Lecce': 0.70,
    'Monza': 0.70,
    'Venezia': 0.68,
    'Empoli': 0.68,
    'Sassuolo': 0.63,
    'Cremonese': 0.63,
    'Pisa': 0.60
}

# Soglie presenze per penalità/bonus
PRESENCE_THRESHOLDS = {
    'P': {
        'excellent': (30, 1.1),   # 30+ presenze = +10%
        'good': (25, 1.0),
        'acceptable': (15, 0.85),
        'low': (10, 0.60),
        'very_low': (0, 0.30)
    },
    'D': {
        'excellent': (32, 1.1),
        'good': (28, 1.0),
        'acceptable': (20, 0.85),
        'low': (15, 0.65),
        'very_low': (0, 0.40)
    },
    'C': {
        'excellent': (32, 1.1),
        'good': (28, 1.0),
        'acceptable': (22, 0.90),
        'low': (15, 0.70),
        'very_low': (0, 0.45)
    },
    'A': {
        'excellent': (30, 1.1),
        'good': (25, 1.0),
        'acceptable': (18, 0.90),  # Anche con poche presenze se segna vale
        'low': (12, 0.75),
        'very_low': (0, 0.50)
    }
}
