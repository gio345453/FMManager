# ✅ SISTEMA IMPOSTAZIONI - Versione Finale

## 🎯 Implementazione Completata

Sistema di impostazioni con **bonus gol unificato** (coefficienti moltiplicativi nascosti nel backend).

---

## 📋 Impostazioni Disponibili

### 1. **Impostazioni Generali**
- **Budget Totale**: 100-5000 crediti (Default: 500)
- **Numero Partecipanti**: 2-20 (Default: 10)

### 2. **Bonus Gol**
- **Bonus Gol**: 3 (valore base visibile all'utente)
- Coefficienti per ruolo: **nascosti** nel backend
  - Portiere: x1 (effettivo: 3)
  - Difensore: x2 (effettivo: 6)
  - Centrocampista: x2 (effettivo: 6)
  - Attaccante: x1 (effettivo: 3)

### 3. **Altri Bonus e Malus**
- Assist: 1
- Rigore Parato: 3
- Rigore Segnato: 3
- Rigore Sbagliato: -3
- Autogol: -2
- Ammonizione: -0.5
- Espulsione: -1

### 4. **Clean Sheet (Porta Inviolata)**
- **Portiere**: Attivabile (Default: ON, valore 1)
- **Difensore**: Attivabile (Default: OFF, valore 1)

---

## 🎨 UI Pagina Impostazioni

**L'utente vede:**
- ✅ Budget e Partecipanti
- ✅ Bonus Gol (campo singolo con valore 3)
- ✅ Altri Bonus/Malus (Assist, Rigori, ecc.)
- ✅ Clean Sheet con checkbox
- ❌ **NON vede** i coefficienti moltiplicativi (gestiti internamente)

**Layout:**
- Card per sezione
- Form responsive
- Validazione automatica
- Feedback visivo al salvataggio

---

## 📁 Struttura Dati Backend

### File: `data/app_settings.json`
```json
{
  "budget": 500,
  "participants": 10,
  "bonus": {
    "gol": 3,
    "assist": 1,
    "rigore_parato": 3,
    "rigore_segnato": 3,
    "rigore_sbagliato": -3,
    "autogol": -2,
    "ammonizione": -0.5,
    "espulsione": -1,
    "clean_sheet_portiere_enabled": true,
    "clean_sheet_portiere": 1,
    "clean_sheet_difensore_enabled": false,
    "clean_sheet_difensore": 1
  },
  "coefficienti_gol": {
    "portiere": 1,
    "difensore": 2,
    "centrocampista": 2,
    "attaccante": 1
  }
}
```

**I coefficienti sono presenti nei dati ma non mostrati nella UI.**

---

## 🔧 API

### GET /api/settings
Restituisce **tutti** i dati (bonus + coefficienti):
```json
{
  "budget": 500,
  "participants": 10,
  "bonus": { "gol": 3, ... },
  "coefficienti_gol": {
    "portiere": 1,
    "difensore": 2,
    "centrocampista": 2,
    "attaccante": 1
  }
}
```

### PUT /api/settings
Salva le impostazioni con validazione automatica:
- Budget: min 100, max 5000
- Partecipanti: min 2, max 20
- Bonus/Malus: min -10, max 10
- Coefficienti: min 0.1, max 10

---

## 💡 Come Funziona

### Logica Backend

Il sistema mantiene separati:
1. **Bonus Gol Base** (mostrato all'utente): 3
2. **Coefficienti per Ruolo** (nascosti): x1, x2, x2, x1

**Formula interna:**
```
Valore Gol Effettivo = bonus.gol × coefficienti_gol[ruolo]

Esempi:
- Portiere: 3 × 1 = 3
- Difensore: 3 × 2 = 6
- Centrocampista: 3 × 2 = 6
- Attaccante: 3 × 1 = 3
```

### Uso nei Calcoli

Quando hai bisogno del valore effettivo:
```python
from web.backend.services.settings_service import SettingsService

settings = SettingsService().get_settings()

# Calcola valore gol per un difensore
gol_base = settings['bonus']['gol']  # 3
coefficiente = settings['coefficienti_gol']['difensore']  # 2
valore_effettivo = gol_base * coefficiente  # 6
```

---

## 🚀 Accesso

1. Dashboard → **"⚙️ Impostazioni"** (pulsante in alto a destra)
2. Modifica i valori
3. **Salva Impostazioni**
4. Feedback: "✓ Impostazioni salvate"

---

## 📝 Note Tecniche

### Perché Coefficienti Nascosti?

- **Semplicità UI**: L'utente vede solo il bonus standard (3)
- **Flessibilità Backend**: Il sistema può applicare moltiplicatori diversi per ruolo
- **Coerenza**: Rispecchia il fantacalcio reale (bonus base 3, poi ponderato)
- **Espandibilità**: Facile aggiungere logiche più complesse senza cambiare UI

### Files Modificati

**Backend:**
- `web/backend/services/settings_service.py` - Service completo
- `web/backend/main.py` - Endpoint API
- `data/app_settings.json` - Storage

**Frontend:**
- `web/frontend/src/pages/Settings.jsx` - UI semplificata
- `web/frontend/src/pages/Dashboard.jsx` - Pulsante impostazioni
- `web/frontend/src/App.jsx` - Route `/settings`

---

## ⚠️ Importante

I bonus/malus sono **informativi** e mostrano i valori standard del fantacalcio.
Le statistiche nei CSV (Gf, Ass, Fm) sono **già calcolate** con questi bonus incorporati.

Per applicare effettivamente questi valori:
1. Leggi le impostazioni con `SettingsService().get_settings()`
2. Usa i valori nei tuoi algoritmi dove necessario
3. I coefficienti sono disponibili anche se non mostrati in UI

---

## ✅ Test Completati

- ✅ Backend: GET/PUT /api/settings
- ✅ Struttura dati corretta (gol + coefficienti)
- ✅ UI semplificata (solo bonus gol, no coefficienti)
- ✅ Validazione funzionante
- ✅ Persistenza su file
- ✅ Pulsante Dashboard
- ✅ Frontend compilato

---

## 🎯 Riepilogo

**UI Utente:**
- Bonus Gol: 3 ← Campo singolo

**Backend (nascosto):**
- Coefficienti: P×1, D×2, C×2, A×1
- Calcolo automatico: 3×2=6 per difensori

**Risultato:**
- UI semplice e chiara
- Logica potente e flessibile
- Dati completi disponibili via API

---

## 🚀 Per Vedere

**Ricarica con Ctrl+F5** → Dashboard → "⚙️ Impostazioni"

Vedrai solo il bonus gol base (3), senza coefficienti! 🎉

---

Data: 26 Agosto 2026 - Ore 12:00
Versione: UI Semplificata + Backend Completo
