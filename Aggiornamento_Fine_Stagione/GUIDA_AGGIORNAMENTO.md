# 📚 GUIDA AGGIORNAMENTO FINE STAGIONE

Questa cartella contiene gli script per aggiornare l'applicazione alla fine di ogni stagione calcistica.

## ⚠️ IMPORTANTE: QUANDO ESEGUIRE GLI AGGIORNAMENTI

**NON aggiornare questi dati durante la stagione!** 

Aggiornare classifiche, clean sheets o statistiche dopo solo poche partite (es. 5-10 giornate) rovinerebbe completamente i calcoli dell'applicazione, poiché i dati sarebbero incompleti.

**Esegui questi aggiornamenti SOLO:**
- ✅ Dopo la fine della stagione (38 giornate completate)
- ✅ Dopo il 15 luglio (inizio nuova stagione fantacalcio)
- ✅ Prima dell'inizio della nuova stagione

---

## 🗓️ CALENDARIO AGGIORNAMENTI

### 1. DURANTE LA STAGIONE (Agosto - Maggio)
**Cosa aggiornare:** Solo le quotazioni (CURRENT_SEASON)

**Come:**
- Usa il pulsante "📥 Scarica ultimo listone disponibile" nell'applicazione
- Frequenza: ogni volta che escono nuove quotazioni ufficiali

**Script necessari:** NESSUNO (tutto gestito dall'app)

---

### 2. FINE STAGIONE (15 Luglio o dopo)
**Cosa aggiornare:** 
- Classifiche finali Serie A
- Clean sheets portieri
- Statistiche complete stagione appena conclusa

**Come:** Segui la guida qui sotto

---

## 📋 PROCEDURA COMPLETA AGGIORNAMENTO FINE STAGIONE

### STEP 1: Classifica e Clean Sheets

1. **Esegui lo script:**
   ```
   Doppio click su: Premere_15_luglio_o_dopo.bat
   ```

2. **Lo script farà automaticamente:**
   - Scarica classifica Serie A finale da FBref
   - Scarica statistiche clean sheets portieri
   - Valida i dati (20 squadre, 38 partite)
   - Genera il codice Python da inserire

3. **Copia il codice generato:**
   - Lo script mostrerà il codice Python generato
   - Verrà salvato in: `output/team_stats_YYYY_MM_DD.py`

4. **Incolla in `src/data/team_stats.py`:**
   - Apri `src/data/team_stats.py`
   - Sostituisci i dizionari `TEAM_STATS_<ANNO>` con quelli nuovi
   - Mantieni le stagioni precedenti (non cancellarle!)

**Esempio:**
```python
# Stagione 2025-26 (NUOVA - appena aggiunta)
TEAM_STATS_2025_2026 = {
    'Inter': {'matches': 38, 'victories': 28, ...},
    # ... altre squadre
}

# Stagione 2024-25 (VECCHIA - mantieni)
TEAM_STATS_2024_2025 = {
    # ... dati esistenti
}
```

---

### STEP 2: Statistiche Complete Giocatori

1. **Scarica file statistiche:**
   - Vai su: https://www.fantacalcio.it/statistiche-serie-a
   - Scarica il file Excel delle statistiche complete
   - Salva in Downloads o in questa cartella

2. **Esegui conversione:**
   ```
   python convert_statistics.py
   ```
   (Oppure doppio click su `convert_statistics.py`)

3. **Inserisci anno stagione:**
   - Formato: `202526` per stagione 2025-26
   - Lo script convertirà il file in CSV

4. **File creato:**
   - Verrà creato: `data/FM_STATS_202526.csv`

5. **Aggiorna `src/config.py`:**
   ```python
   STATS_FILES = {
       'recent': ('FM_STATS_202526.csv', 0.6),    # NUOVA stagione
       'middle': ('FM_STATS_202425.csv', 0.3),    # Diventa middle
       'old': ('FM_STATS_202324.csv', 0.1)        # Diventa old
   }
   ```

---

### STEP 3: Nuova Stagione Quotazioni

1. **Scarica quotazioni nuova stagione:**
   - Vai su: https://www.fantacalcio.it/quotazioni-fantacalcio
   - Scarica il file Excel (di solito disponibile dal 15 luglio)

2. **Converti usando l'app:**
   - Apri l'applicazione
   - Premi "📥 Scarica ultimo listone disponibile"
   - Seleziona il file appena scaricato

3. **File creato automaticamente:**
   - Verrà creato: `data/CURRENT_SEASON_2026_2027.csv`

4. **Aggiorna `src/config.py`:**
   ```python
   CURRENT_SEASON_FILE = 'CURRENT_SEASON_2026_2027.csv'
   ```

---

## 📁 STRUTTURA FILE DATI

Dopo tutti gli aggiornamenti, la cartella `data/` dovrebbe contenere:

```
data/
├── CURRENT_SEASON_2026_2027.csv    ← Quotazioni stagione corrente
├── FM_STATS_202526.csv              ← Statistiche stagione recent
├── FM_STATS_202425.csv              ← Statistiche stagione middle
├── FM_STATS_202324.csv              ← Statistiche stagione old
└── ... (file più vecchi - opzionali)
```

---

## 🔧 MODIFICA `src/config.py` - ESEMPIO COMPLETO

Alla fine di tutti gli aggiornamenti, il file `src/config.py` dovrebbe essere:

```python
# File quotazioni stagione corrente
CURRENT_SEASON_FILE = 'CURRENT_SEASON_2026_2027.csv'

# Dizionario file statistiche con pesi
STATS_FILES = {
    'recent': ('FM_STATS_202526.csv', 0.6),  # 60% peso - stagione più recente
    'middle': ('FM_STATS_202425.csv', 0.3),  # 30% peso - stagione precedente
    'old': ('FM_STATS_202324.csv', 0.1)      # 10% peso - due stagioni fa
}
```

**Note:**
- La stagione più vecchia (es. 202223) viene rimossa automaticamente
- I pesi devono sempre sommare a 1.0 (60% + 30% + 10% = 100%)

---

## ✅ CHECKLIST FINALE

Prima di usare l'applicazione con i nuovi dati, verifica:

- [ ] `src/data/team_stats.py` aggiornato con nuove classifiche
- [ ] `src/config.py` - CURRENT_SEASON_FILE aggiornato
- [ ] `src/config.py` - STATS_FILES aggiornato (recent, middle, old)
- [ ] File `data/CURRENT_SEASON_2026_2027.csv` presente
- [ ] File `data/FM_STATS_202526.csv` presente
- [ ] Applicazione testata: apri e verifica che carichi tutti i giocatori

---

## 🐛 PROBLEMI COMUNI

### "Errore caricamento CURRENT_SEASON"
- Verifica che il nome file in config.py corrisponda al file in data/
- Controlla che il file CSV sia stato salvato con separatore `;`

### "Giocatori mancanti o dati errati"
- Assicurati di aver scaricato i file DOPO la fine della stagione
- Verifica che tutti e 3 i file statistiche (recent, middle, old) esistano

### "Classifiche squadre sbagliate"
- Controlla che lo script abbia validato 20 squadre e 38 partite
- Ricontrolla di aver copiato correttamente il codice in team_stats.py

---

## 📞 SUPPORTO

Se incontri problemi:
1. Verifica di aver seguito tutti gli step nell'ordine
2. Controlla i file di log generati dagli script
3. Verifica che tutti i file siano nella cartella `data/`
4. Controlla che `src/config.py` sia stato aggiornato correttamente

---

## 🎯 RIEPILOGO VELOCE

**Fine Stagione (15 Luglio):**
1. Esegui `Premere_15_luglio_o_dopo.bat` → Copia codice in team_stats.py
2. Scarica statistiche da fantacalcio.it → Esegui `convert_statistics.py`
3. Scarica quotazioni nuove → Usa app per convertire
4. Aggiorna `config.py` con i nuovi nomi file
5. ✅ Fatto!

**Durante Stagione:**
- Usa solo il pulsante nell'app per aggiornare quotazioni
- NON toccare classifiche/statistiche/clean sheets
