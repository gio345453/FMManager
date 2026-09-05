# 📚 GUIDA AGGIORNAMENTO FINE STAGIONE

Questa cartella contiene gli script per aggiornare l'applicazione alla fine di ogni stagione calcistica.

## 🚀 NOVITÀ: AUTOMAZIONE COMPLETA

**Da questa versione, l'aggiornamento è completamente automatico!**

✅ **Non servono più modifiche manuali a:**
- `src/config.py` (file CSV risolti automaticamente)
- URL FBref (generati dinamicamente)
- Anno/stagione (calcolati dalla data)

✅ **Merge sicuro:**
- Dati esistenti preservati se download fallisce
- Validazione automatica prima di salvare

📚 **Documentazione tecnica completa:** `AUTOMAZIONE_STAGIONALE.md`

---

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

**🤖 PROCEDURA AUTOMATICA - UN SOLO COMANDO:**

```
Doppio click su: Premere_15_luglio_o_dopo.bat
```

**Questo script farà AUTOMATICAMENTE:**
1. ✅ Download dati FBref (ultime 3 stagioni concluse)
2. ✅ Validazione automatica (minimo 18 squadre Serie A)
3. ✅ Merge sicuro (preserva dati se download fallisce)
4. ✅ Calcolo forza squadre (formula 40/30/20/10):
   - 40% produzione recente (gol fatti/subiti vs media lega)
   - 30% forza reparti (da statistiche giocatori)
   - 20% classifica stagione precedente
   - 10% storico lungo Serie A
5. ✅ Aggiornamento `team_strength.json` (pronto all'uso)

**NESSUN intervento manuale richiesto!**

L'applicazione userà automaticamente i nuovi dati al prossimo avvio.

---

## 📋 PROCEDURA DETTAGLIATA (OPZIONALE)

Se preferisci eseguire i comandi singolarmente o hai bisogno di controllo avanzato:

### Comando Principale (Raccomandato)

```bash
python scripts/update_team_strength.py --refresh-team-stats
```

Questo comando esegue la pipeline completa in 3 fasi:
1. Download FBref con merge sicuro
2. Calcolo forza reparti da giocatori
3. Calcolo produzione storica e unificazione finale

### Comandi Avanzati

**Download solo dati FBref:**
```bash
# Automatico (ultime 3 stagioni concluse)
python data/Calendario/download_team_stats.py

# Stagioni specifiche
python data/Calendario/download_team_stats.py --seasons 2025-26 2024-25 2023-24

# Più stagioni storiche
python data/Calendario/download_team_stats.py --history-count 5
```

**Ricalcolo senza download:**
```bash
python scripts/update_team_strength.py
```

**Calcolo forza reparti con override:**
```bash
python scripts/calculate_department_strength.py \
  --current-season-file data/stats/CURRENT_SEASON_2026_2027.csv \
  --stats-file data/stats/FM_STATS_202526.csv
```

---

## 📁 FILE AGGIORNATI AUTOMATICAMENTE

Dopo l'esecuzione dello script, questi file saranno aggiornati:

```
data/Calendario/
├── team_strength.json                    ← PRONTO ALL'USO (v3)
├── team_historical_strength.json         ← Componenti storiche intermedie
└── team_department_strength.json         ← Forza reparti da giocatori

Aggiornamento_Fine_Stagione/
└── team_stats_fbref.json                 ← Dati FBref con metadata
```

**L'applicazione userà automaticamente questi file, nessuna modifica manuale richiesta!**

---

## 🎯 COSA È STATO AUTOMATIZZATO

### ✅ Risoluzione Stagioni
- **Stagione corrente**: calcolata dalla data (cambio a luglio)
- **Ultima conclusa**: Serie A più recente completata
- **Stagioni storiche**: ultime 3 concluse automaticamente

### ✅ File CSV Dinamici
- `CURRENT_SEASON_*.csv`: trovato automaticamente il più recente
- `FM_STATS_*.csv`: trovati automaticamente per ultime 3 stagioni
- **Non serve più modificare `src/config.py`!**

### ✅ URL FBref Dinamici
- URL generati automaticamente per ogni stagione
- Stagione corrente: `https://fbref.com/en/comps/11/Serie-A-Stats`
- Stagioni passate: formato esteso automatico

### ✅ Merge Sicuro
- Dati esistenti preservati se download fallisce
- Validazione automatica (≥18 squadre, dati validi)
- Metadata completi (fonte, data, qualità)

### ✅ Formula Aggiornata
- **40%** produzione recente (gol per partita vs media lega)
- **30%** forza reparti (da statistiche giocatori)
- **20%** classifica stagione precedente
- **10%** storico lungo Serie A (ultimi 3 anni)

---

## 📝 STEP MANUALI RIMASTI (Solo se necessario)

### STEP 1: Statistiche Complete Giocatori

**Solo se il file FM_STATS della nuova stagione non esiste ancora:**

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
   - Verrà creato: `data/stats/FM_STATS_202526.csv`

5. **Riesegui aggiornamento:**
   ```bash
   python scripts/update_team_strength.py --refresh-team-stats
   ```

---

### STEP 2: Nuova Stagione Quotazioni

**Solo all'inizio della nuova stagione (Agosto):**

1. **Scarica quotazioni nuova stagione:**
   - Vai su: https://www.fantacalcio.it/quotazioni-fantacalcio
   - Scarica il file Excel (di solito disponibile dal 15 luglio)

2. **Converti usando l'app:**
   - Apri l'applicazione
   - Premi "📥 Scarica ultimo listone disponibile"
   - Seleziona il file appena scaricato

3. **File creato automaticamente:**
   - Verrà creato: `data/stats/CURRENT_SEASON_2026_2027.csv`

**L'app troverà automaticamente questo file, non serve modificare `config.py`!**

---

## ✅ CHECKLIST FINALE

Prima di usare l'applicazione con i nuovi dati, verifica:

- [ ] Script `Premere_15_luglio_o_dopo.bat` eseguito con successo
- [ ] File `data/Calendario/team_strength.json` aggiornato (controlla data)
- [ ] File `data/stats/CURRENT_SEASON_YYYY_YYYY.csv` presente (se nuova stagione)
- [ ] File `data/stats/FM_STATS_YYYYYY.csv` presenti (almeno 3 stagioni)
- [ ] Applicazione testata: apri e verifica che carichi tutti i giocatori
- [ ] Fixture difficulty coerenti (verifica alcuni giocatori)

**Non serve più verificare `src/config.py` - tutto automatico!**

---

## 🐛 PROBLEMI COMUNI

### "Download FBref fallito (403 Forbidden)"
- **Soluzione:** Il sistema ha preservato i dati esistenti (merge sicuro)
- FBref può bloccare scraping automatico
- Riprova tra 5-10 minuti
- Verifica connessione internet
- I dati esistenti restano validi e utilizzabili

### "Nessun file CURRENT_SEASON trovato"
- **Soluzione:** Crea il file usando l'app ("Scarica listone")
- Oppure specifica manualmente con `--current-season-file`
- Il file sarà trovato automaticamente al prossimo aggiornamento

### "Nessun file FM_STATS recente trovato"
- **Soluzione:** Scarica e converti statistiche da fantacalcio.it
- Usa `convert_statistics.py` per creare il CSV
- Il file sarà trovato automaticamente

### "Giocatori mancanti o dati errati"
- Assicurati di aver scaricato i file DOPO la fine della stagione
- Verifica che almeno 2 file FM_STATS esistano
- Controlla che CURRENT_SEASON sia della stagione corretta

### "Classifiche squadre sbagliate"
- Lo script valida automaticamente 20 squadre Serie A
- Se dati non validi, usa quelli esistenti (merge sicuro)
- Verifica output dello script per messaggi di validazione

---

## 🆕 DIFFERENZE RISPETTO ALLA VERSIONE PRECEDENTE

### ❌ NON SERVE PIÙ:
- ~~Modificare manualmente `src/config.py`~~
- ~~Copiare codice Python da `scripts/output/`~~
- ~~Aggiornare manualmente `team_stats.py`~~
- ~~Specificare anno/stagione negli script~~
- ~~Generare URL FBref manualmente~~

### ✅ ORA È AUTOMATICO:
- Risoluzione stagioni dalla data
- Ricerca file CSV più recenti
- Download dati FBref con URL dinamici
- Calcolo forza squadra con nuova formula
- Merge sicuro e validazione
- Aggiornamento file runtime

---

## 📞 SUPPORTO

Se incontri problemi:
1. Controlla l'output dello script per messaggi di errore dettagliati
2. Leggi `AUTOMAZIONE_STAGIONALE.md` per dettagli tecnici
3. Verifica che tutti i file siano nella cartella `data/stats/`
4. Esegui i test: `python -m pytest tests/test_season_resolution.py -v`

---

## 🎯 RIEPILOGO VELOCE

**Fine Stagione (15 Luglio):**
1. ✅ Esegui `Premere_15_luglio_o_dopo.bat`
2. ✅ Attendi completamento automatico (~5 minuti)
3. ✅ (Opzionale) Scarica nuovo listone quotazioni se disponibile
4. ✅ (Opzionale) Scarica/converti statistiche FM se disponibili
5. ✅ Fatto! Nessuna modifica manuale richiesta

**Durante Stagione:**
- Usa solo il pulsante nell'app per aggiornare quotazioni
- NON eseguire lo script di aggiornamento fine stagione

**Documentazione Tecnica:**
- `AUTOMAZIONE_STAGIONALE.md` - Guida completa sistema automatico
- Test: `tests/test_season_resolution.py`
- Test: `tests/test_fbref_downloader.py`
