"""
FantaCalcio Analyzer - Applicazione per analisi giocatori
Versione con interfaccia moderna CustomTkinter
Analizza le statistiche dei giocatori su 3 stagioni con ponderazione:
- 60% stagione più recente
- 30% stagione media
- 10% stagione più vecchia

Le stagioni vengono caricate automaticamente dalla configurazione (config.py).
"""

from src.ui.app_modern import main

if __name__ == "__main__":
    main()
