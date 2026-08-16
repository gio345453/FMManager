# 🎯 GUIDA RAPIDA - Sistema Completo Aggiornamento Stagioni

**Per utenti finali - Tutto quello che devi sapere**

---

## 📅 **QUANDO: 15 Luglio di Ogni Anno**

---

## ⚡ **PROCEDURA ULTRA-RAPIDA**

### **3 Passi Totali:**

```
1️⃣ Doppio click su: Premere_15_luglio_o_dopo.bat
        ↓
   (Lo script lavora per te - 1 minuto)
        ↓
2️⃣ Copia 2 file generati (2 minuti)
        ↓
3️⃣ Testa app (1 minuto)
        ↓
   ✅ FATTO! (4 minuti totali)
```

---

## 🎬 **PASSO-PASSO DETTAGLIATO**

### **PREPARAZIONE (Una Tantum)**

Prima volta che usi il sistema:

1. **Aggiungi i nuovi file CSV** nella cartella `data/`:
   ```
   data/CURRENT_SEASON_2027_2028.csv
   data/FM_STATS_202627.csv
   ```

2. **Aggiorna `src/config.py`** (4 righe):
   ```python
   CURRENT_SEASON_FILE = "CURRENT_SEASON_2027_2028.csv"
   STATS_FILES = {
       'recent': ('FM_STATS_202627.csv', 0.60),
       'middle': ('FM_STATS_202526.csv', 0.30),
       'old': ('FM_STATS_202425.csv', 0.10)
   }
   ```

### **AGGIORNAMENTO DATI (Ogni Anno)**

**STEP 1: Esegui il .BAT** (1 minuto - automatico)

```
📁 Cartella principale progetto
    ├── Premere_15_luglio_o_dopo.bat  ← DOPPIO CLICK
```

Il file .bat farà:
- ✅ Backup automatico
- ✅ Download classifica FBref
- ✅ Download clean sheets FBref
- ✅ Validazione dati
- ✅ Generazione codice Python

**STEP 2: Copia i File Generati** (2 minuti)

```
A. Apri: scripts/output/team_stats_generated_*.py
   Copia il dizionario CLASSIFICA_REALE_CURRENT_SEASON
   Incolla in: src/data/team_stats.py (riga ~12)

B. Apri: scripts/output/clean_sheets_generated_*.py
   Copia il dizionario CLEAN_SHEETS_CURRENT_SEASON
   Incolla in: src/data/clean_sheets_data.py (riga ~6)
```

**STEP 3: Testa** (1 minuto)

```bash
python main_modern.py
```

Verifica:
- ✅ Dashboard mostra "Serie A 2027/2028"
- ✅ Classifica squadre corretta
- ✅ Grafici mostrano 2024-25, 2025-26, 2026-27

---

## 📊 **COSA È AUTOMATICO**

### **✅ Automatico (Zero Lavoro):**
- Estrazione anni dai nomi file
- Aggiornamento tutte le UI
- Aggiornamento titoli e label
- Calcolo statistiche ponderate
- Grafici trend
- Download dati FBref
- Validazione dati
- Backup file

### **✏️ Manuale (2 Minuti):**
- Aggiungere file CSV nuovi
- Aggiornare config.py (4 righe)
- Eseguire .bat
- Copiare 2 dizionari

---

## 🗂️ **STRUTTURA FILE**

```
FantaCalcio-App/
│
├── Premere_15_luglio_o_dopo.bat    ← 🔴 ESEGUI QUESTO
│
├── data/
│   ├── CURRENT_SEASON_2027_2028.csv ← Aggiungi nuovo
│   ├── FM_STATS_202627.csv          ← Aggiungi nuovo
│   ├── FM_STATS_202526.csv
│   └── ...
│
├── src/
│   ├── config.py                    ← Modifica (4 righe)
│   └── data/
│       ├── team_stats.py            ← Copia dizionario qui
│       └── clean_sheets_data.py     ← Copia dizionario qui
│
├── scripts/
│   ├── update_season_data.py        ← Script (non toccare)
│   └── output/                      ← File generati qui
│       ├── team_stats_generated_*.py
│       └── clean_sheets_generated_*.py
│
└── Guide/
    ├── ISTRUZIONI_BAT.md            ← Guida .bat
    ├── SCALABILITY_GUIDE.md         ← Guida completa
    └── QUICK_START_USER.md          ← Questo file
```

---

## ⏱️ **TEMPO RICHIESTO**

| Operazione | Prima Volta | Anni Successivi |
|------------|-------------|-----------------|
| Setup dipendenze | 2 min | 0 min |
| Aggiorna config.py | 2 min | 2 min |
| Esegui .bat | 1 min | 1 min |
| Copia dizionari | 2 min | 2 min |
| Test app | 1 min | 1 min |
| **TOTALE** | **8 min** | **6 min** |

---

## 🎯 **CHECKLIST ANNUALE**

```
□ 1. Ottenuto file CSV nuova stagione?
□ 2. Aggiunti in cartella data/?
□ 3. Aggiornato src/config.py (4 righe)?
□ 4. Eseguito Premere_15_luglio_o_dopo.bat?
□ 5. Script completato senza errori?
□ 6. Controllato preview dati?
□ 7. Copiato dizionario classifica?
□ 8. Copiato dizionario clean sheets?
□ 9. Testato main_modern.py?
□ 10. Verificato anni corretti nelle UI?
```

---

## ⚠️ **SE QUALCOSA VA STORTO**

### **1. Python non trovato**
```
Installa: https://www.python.org/downloads/
✅ Spunta "Add Python to PATH"
Riavvia PC
```

### **2. Script fallisce**
```
Controlla internet
Aspetta 5-10 minuti
Riprova
Se persiste → Vedi SCALABILITY_GUIDE.md
```

### **3. Dati strani**
```
Controlla nomi squadre in CSV
Aggiorna mapping in update_season_data.py
Riesegui .bat
```

### **4. App non parte**
```
Verifica backup in src/data/*.backup.*
Ripristina file originali
Riprova procedura
```

---

## 📚 **DOCUMENTAZIONE COMPLETA**

### **Per Uso Normale:**
- ✅ `ISTRUZIONI_BAT.md` - Come usare il .bat
- ✅ `QUICK_START_USER.md` - Questo file

### **Per Approfondire:**
- 📖 `SCALABILITY_GUIDE.md` - Guida tecnica completa
- 📖 `scripts/README.md` - Documentazione script

### **Per Sviluppatori:**
- 🔧 `SCALABILITY_CHANGES_REPORT.md` - Report modifiche
- 🔧 `IMPLEMENTATION_SUMMARY.md` - Riepilogo implementazione

---

## 🎉 **VANTAGGI DEL SISTEMA**

| Aspetto | Senza Sistema | Con Sistema |
|---------|---------------|-------------|
| Tempo aggiornamento | 30 minuti | 6 minuti |
| Rischio errori | 🔴 Alto | 🟢 Minimo |
| File da modificare | 8+ file | 3 file |
| Backup automatico | ❌ | ✅ |
| Validazione dati | ❌ | ✅ |
| Difficoltà | 🔴 Media | 🟢 Facile |

---

## 💡 **TIPS PRO**

### **Prima dell'aggiornamento:**
- ✅ Fai commit su git (se usi)
- ✅ Testa app attuale (per confronto)
- ✅ Leggi ISTRUZIONI_BAT.md

### **Durante l'aggiornamento:**
- ✅ Non chiudere finestra .bat prematuramente
- ✅ Leggi messaggi di errore
- ✅ Verifica preview dati

### **Dopo l'aggiornamento:**
- ✅ Testa tutti i grafici
- ✅ Verifica dashboard squadre
- ✅ Controlla dettagli giocatore
- ✅ Fai commit modifiche

---

## 🗓️ **TIMELINE ANNUALE**

```
Giugno
└─> Fine campionato

10-15 Luglio
└─> Ottieni file CSV nuova stagione
    (da Fantagazzetta, FantaCalcio.it, etc.)

15 Luglio
└─> 🎯 GIORNO IDEALE PER AGGIORNAMENTO
    ├─> Esegui Premere_15_luglio_o_dopo.bat
    └─> Copia dizionari generati

16-30 Luglio
└─> Backup - Puoi ancora aggiornare

1 Agosto
└─> Inizio nuova stagione
```

---

## ✅ **STATO SISTEMA**

🟢 **PRONTO ALL'USO**

- ✅ Script funzionante
- ✅ Backup automatico
- ✅ Validazione integrata
- ✅ Documentazione completa
- ✅ File .bat user-friendly

**Prossimo utilizzo:** 15 Luglio 2027 🗓️

---

## 🆘 **AIUTO**

**Hai problemi?**

1. Leggi `ISTRUZIONI_BAT.md`
2. Controlla sezione "Risoluzione Problemi"
3. Verifica file backup (`.backup.*`)
4. Consulta `SCALABILITY_GUIDE.md`

**Tutto chiaro? Sei pronto per il 2027! 🚀**
