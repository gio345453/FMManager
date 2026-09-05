# FMManager Web App

Applicazione web moderna per la gestione del Fantacalcio con React frontend e FastAPI backend.

## 🚀 Avvio Rapido

### Windows
```bash
start_backend.bat
```

### Linux/Mac
```bash
./start_backend.sh
```

Oppure manualmente:
```bash
cd web/backend
python startup.py
```

Il backend sarà disponibile su: http://localhost:8000

### Frontend
In un altro terminale:
```bash
cd web/frontend
npm install
npm run dev
```

Il frontend sarà disponibile su: http://localhost:5173

## 📋 Funzionalità Automatiche all'Avvio

Ogni volta che avvii il backend con `startup.py`, vengono eseguiti automaticamente:

1. **Download Tiratori** - Scarica i rigoristi e tiratori di piazzati da Fantacalcio.it (una volta ogni 24 ore)
2. **Assegnazione Tag Automatici**:
   - Tag "rigorista" al primo rigorista di ogni squadra
   - Tag "tiratore piazzati" al primo tiratore di calci piazzati

## 🎯 Funzionalità Principali

- **Ricerca Giocatori** - Filtri avanzati per ruolo, squadra, FM, prezzo, tag
- **Build Rosa** - Ottimizzazione con algoritmo knapsack
- **Confronto Giocatori** - Confronta 2-3 giocatori side-by-side
- **Statistiche Ponderate** - Overall calcolato sulle ultime 3 stagioni
- **Tag Automatici** - Rigoristi e tiratori piazzati evidenziati
- **Aggiornamento Listone** - Upload Excel quotazioni Fantacalcio.it
- **Aggiornamento Fine Stagione** - Pulsante temporale (15 luglio - 18 agosto)

## 📂 Struttura

```
web/
├── backend/          # FastAPI backend
│   ├── main.py      # API endpoints
│   ├── startup.py   # Script avvio con task automatici
│   ├── services/    # Business logic
│   └── schemas.py   # Pydantic models
├── frontend/         # React + Vite
│   └── src/
│       ├── pages/   # Pagine
│       ├── api/     # Client API
│       └── App.jsx
```

## 🛠️ Stack Tecnologico

**Backend:**
- FastAPI (Python 3.11+)
- Pandas per elaborazione dati
- Logica esistente da app Python desktop

**Frontend:**
- React 18
- Vite
- React Router
- CSS moderno

## 📝 Note

- I dati sono salvati in file locali (CSV/JSON)
- Il backend usa la stessa logica dell'app Python desktop
- Compatibile con Windows, Linux, macOS
