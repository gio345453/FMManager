# FantaCalcio Analyzer

Applicazione Windows per l'analisi dei giocatori del fantacalcio con statistiche ponderate su 3 stagioni.

## 🚀 Avvio Rapido

**Avvia l'applicazione:**
```
Doppio click su: avvia_app.bat
```

**Prima volta?** Leggi la [Guida Rapida](docs/utente/QUICK_START_USER.md)

---

## ✨ Caratteristiche Principali

### 📊 Analisi Intelligente
- **Ponderazione automatica** delle statistiche su 3 stagioni:
  - 60% stagione più recente
  - 30% stagione precedente
  - 10% due stagioni fa
- **Calcolo prezzi** basato su budget e statistiche ponderate
- **Sistema Overall (OVR)** per valutazione complessiva giocatori

### 🔍 Ricerca e Filtri
- Filtri per ruolo (P, D, C, A)
- Filtri per squadra
- Ricerca per nome giocatore
- Ordinamento per qualsiasi colonna
- Sistema preferiti e note personalizzate

### 📈 Visualizzazioni Avanzate
- **Grafici Trend Stagionali**: Evoluzione Fm, Mv, Gf, Assist per giocatore
- **Confronto Giocatori**: Confronta fino a 3 giocatori con grafici interattivi
- **Dashboard Squadre**: Statistiche aggregate e classifiche reali
- **Dettagli Squadra**: Info complete su rosa, clean sheets, forza difensiva

### 🔄 Aggiornamenti Facili
- **Durante stagione**: Pulsante per scaricare nuove quotazioni
- **Fine stagione**: Script automatici per aggiornare tutto (15 luglio - 18 agosto)

---

## 📁 Struttura Progetto

```
FantaCalcio-Analyzer/
│
├── 🚀 avvia_app.bat                      # Avvio rapido applicazione
├── 📄 main_modern.py                     # Entry point applicazione
├── 📦 requirements.txt                   # Dipendenze Python
├── 📖 README.md                          # Questo file
│
├── 📂 src/                               # Codice sorgente applicazione
│   ├── config.py                         # Configurazione globale
│   ├── data_processor.py                 # Processamento dati
│   ├── data/                             # Business logic
│   │   ├── cache.py                      # Cache dati
│   │   ├── calculator.py                 # Calcolo statistiche
│   │   ├── price_calculator.py           # Calcolo prezzi
│   │   ├── player_notes.py               # Note giocatori
│   │   ├── favorites_manager.py          # Gestione preferiti
│   │   ├── team_stats.py                 # Statistiche squadre
│   │   └── ...
│   └── ui/                               # Interfaccia grafica
│       ├── app_modern.py                 # Finestra principale
│       ├── player_details.py             # Dettagli giocatore
│       ├── player_comparison.py          # Confronto giocatori
│       ├── team_dashboard.py             # Dashboard squadre
│       └── components/                   # Componenti UI riutilizzabili
│
├── 📂 data/                              # File dati CSV
│   ├── CURRENT_SEASON_2026_2027.csv      # Quotazioni stagione corrente
│   ├── FM_STATS_202526.csv               # Statistiche recent (60%)
│   ├── FM_STATS_202425.csv               # Statistiche middle (30%)
│   └── FM_STATS_202324.csv               # Statistiche old (10%)
│
├── 📂 scripts/                           # Script di utilità
│   ├── convert_quotazioni.py             # Converte Excel quotazioni → CSV
│   └── update_season_data.py             # Aggiorna classifiche/clean sheets
│
├── 📂 Aggiornamento_Fine_Stagione/       # Aggiornamenti annuali (15 lug - 18 ago)
│   ├── 📖 GUIDA_AGGIORNAMENTO.md         # Guida completa aggiornamento
│   ├── 📄 README.txt                     # Istruzioni rapide
│   ├── 🚀 Premere_15_luglio_o_dopo.bat   # Aggiorna classifiche/clean sheets
│   ├── convert_statistics.py             # Converte statistiche Excel → CSV
│   └── update_season_data.py             # Script scraping FBref
│
└── 📂 docs/                              # Documentazione
    ├── utente/                           # Guide per utenti
    │   ├── QUICK_START_USER.md           # Guida rapida utente
    │   ├── ISTRUZIONI_BAT.md             # Come usare file .bat
    │   └── ...
    └── sviluppo/                         # Documentazione tecnica
        ├── SCALABILITY_GUIDE.md          # Come scalare l'app
        ├── REFACTORING_REPORT.md         # Report refactoring
        └── ...
```

---

## 📖 Documentazione

### Per Utenti
- 🚀 [Guida Rapida](docs/utente/QUICK_START_USER.md) - Come iniziare
- ⚙️ [Aggiornamento Stagione](Aggiornamento_Fine_Stagione/GUIDA_AGGIORNAMENTO.md) - Aggiornamenti annuali
- 📥 [Download Quotazioni](docs/utente/CONVERT_QUOTAZIONI_README.md) - Scaricare nuove quotazioni

### Per Sviluppatori
- 🏗️ [Guida Scalabilità](docs/sviluppo/SCALABILITY_GUIDE.md) - Aggiungere nuove stagioni
- 🔧 [Report Refactoring](docs/sviluppo/REFACTORING_REPORT.md) - Architettura codice
- 📊 [Report Ottimizzazioni](docs/sviluppo/OPTIMIZATION_H1_REPORT.md) - Performance

---

## 💻 Installazione

### Requisiti
- Windows 10/11
- Python 3.8 o superiore

### Installazione Dipendenze

**Metodo Automatico (consigliato):**
```
Doppio click su: avvia_app.bat
```
Lo script installerà automaticamente tutte le dipendenze necessarie.

**Metodo Manuale:**
```bash
pip install -r requirements.txt
```

### Dipendenze Principali
- `customtkinter` - UI moderna
- `pandas` - Gestione dati
- `matplotlib` - Grafici
- `openpyxl` - Lettura file Excel
- `beautifulsoup4` - Scraping web (aggiornamenti)

---

## 🎯 Come Usare

### 1. Avvio Applicazione
```
Doppio click su: avvia_app.bat
```

### 2. Funzionalità Principali

**📋 Lista Giocatori**
- Visualizza tutti i giocatori con statistiche ponderate
- Filtra per ruolo, squadra, o cerca per nome
- Ordina cliccando sulle intestazioni colonne
- Aggiungi ai preferiti cliccando sulla stella ⭐

**👤 Dettagli Giocatore**
- Doppio click su un giocatore per vedere dettagli completi
- Visualizza statistiche per ogni stagione
- Aggiungi note e tag personalizzati
- Vedi trend stagionali con grafici

**⚖️ Confronta Giocatori**
- Pulsante "Confronta Giocatori" nella barra principale
- Seleziona fino a 3 giocatori
- Confronta statistiche con grafici interattivi

**🏆 Dashboard Squadre**
- Pulsante "Dashboard Squadre" nella barra principale
- Vedi statistiche aggregate per squadra
- Classifica reale Serie A
- Forza difensiva e clean sheets

### 3. Aggiornamenti

**Durante la Stagione (Agosto - Maggio):**
- Usa pulsante "📥 Scarica ultimo listone disponibile"
- Scarica da: https://www.fantacalcio.it/quotazioni-fantacalcio
- Conversione e refresh automatici

**Fine Stagione (15 Luglio - 18 Agosto):**
- Usa pulsante "⚙️ Aggiornamento Fine Stagione"
- Segui la guida nella cartella aperta
- Aggiorna classifiche, clean sheets e statistiche complete

---

## 🔧 Configurazione

### File config.py

Il file `src/config.py` contiene i parametri principali:

```python
# File quotazioni stagione corrente
CURRENT_SEASON_FILE = 'CURRENT_SEASON_2026_2027.csv'

# File statistiche con pesi
STATS_FILES = {
    'recent': ('FM_STATS_202526.csv', 0.6),  # 60% peso
    'middle': ('FM_STATS_202425.csv', 0.3),  # 30% peso
    'old': ('FM_STATS_202324.csv', 0.1)      # 10% peso
}
```

**Importante:** L'app è scalabile automaticamente - rileva le stagioni dai nomi file.
Quando aggiungi una nuova stagione, aggiorna solo questi nomi file.

---

## ❓ FAQ

**Q: Come aggiorno le quotazioni durante la stagione?**  
A: Usa il pulsante "📥 Scarica ultimo listone disponibile" nell'app. Scarica il file Excel da fantacalcio.it, l'app lo converte automaticamente.

**Q: Posso aggiornare classifiche e statistiche durante la stagione?**  
A: NO! Il pulsante "⚙️ Aggiornamento Fine Stagione" è attivo solo dal 15 luglio al 18 agosto per evitare di corrompere i dati con statistiche incomplete.

**Q: Dove trovo i file dati?**  
A: Tutti i file CSV sono nella cartella `data/`. Non modificarli manualmente.

**Q: Come aggiungo note a un giocatore?**  
A: Doppio click sul giocatore → sezione "Note e Valutazione" → scrivi e salva.

**Q: Posso confrontare giocatori di ruoli diversi?**  
A: Sì, il confronto funziona con qualsiasi combinazione di ruoli.

**Q: Come funziona il calcolo del prezzo?**  
A: Il prezzo è calcolato in base alle statistiche ponderate e al budget impostato. Maggiore è l'Overall, maggiore è la percentuale del budget consigliata.

---

## 🐛 Problemi Comuni

**"Errore caricamento file CSV"**
- Verifica che i file in `data/` esistano
- Controlla che i nomi in `config.py` corrispondano ai file

**"Lista giocatori vuota"**
- Verifica filtri attivi (ruolo/squadra)
- Controlla che `CURRENT_SEASON_FILE` sia configurato correttamente

**"Grafici non si visualizzano"**
- Installa/aggiorna matplotlib: `pip install --upgrade matplotlib`

**"Pulsante aggiornamento disabilitato"**
- Normale! È attivo solo dal 15 luglio al 18 agosto

---

## 🤝 Contribuire

Questo progetto è in sviluppo attivo. Per contribuire:

1. Leggi la documentazione in `docs/sviluppo/`
2. Segui le convenzioni del codice esistente
3. Testa le modifiche prima di committare

---

## 📝 Licenza

Progetto personale per uso interno.

---

## 📞 Supporto

Per problemi o domande:
1. Controlla la sezione FAQ sopra
2. Leggi la documentazione in `docs/utente/`
3. Verifica che tutti i file dati esistano in `data/`

---

**Buona analisi! 🎯⚽**
