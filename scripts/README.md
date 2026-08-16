# 📂 Scripts

Questa cartella contiene script di utilità per la gestione dei dati dell'applicazione.

---

## 📥 convert_quotazioni.py

**Uso:** Converte file Excel quotazioni da fantacalcio.it in CSV compatibile con l'app.

**Quando usare:**
- Durante la stagione, quando escono nuove quotazioni
- Viene chiamato automaticamente dal pulsante "📥 Scarica ultimo listone" nell'app

**Come usare manualmente:**
```bash
python scripts/convert_quotazioni.py
```

**Input:** File Excel da https://www.fantacalcio.it/quotazioni-fantacalcio  
**Output:** `data/CURRENT_SEASON_YYYY_YYYY.csv`

**Caratteristiche:**
- Legge solo il foglio "Tutti"
- Salta la prima riga (header alla riga 2)
- Converte automaticamente le colonne necessarie (Id, R, RM, Nome, Squadra)
- Salva con separatore `;` per compatibilità app

---

## 🔄 update_season_data.py

**Uso:** Scarica e genera codice Python per classifiche Serie A e clean sheets portieri.

**⚠️ Quando usare:**
- **SOLO a fine stagione** (15 luglio - 18 agosto)
- Parte dello script `Premere_15_luglio_o_dopo.bat` in `Aggiornamento_Fine_Stagione/`

**Come funziona:**
1. Scarica classifica Serie A finale da FBref
2. Scarica statistiche clean sheets portieri
3. Valida dati (20 squadre, 38 partite, calcolo punti)
4. Genera codice Python pronto da incollare in `src/data/team_stats.py`

**Output:**
- File: `output/team_stats_YYYY_MM_DD.py`
- Console: Preview top 10 squadre e portieri

---

## ⚠️ IMPORTANTE - Quando Usare Cosa

### Durante la Stagione (Agosto - Maggio)
✅ **USA:** `convert_quotazioni.py` (o pulsante "📥 Scarica ultimo listone" nell'app)  
❌ **NON USARE:** `update_season_data.py`

**Perché?** Aggiornare classifiche/clean sheets a campionato in corso rovinerebbe i calcoli con dati incompleti.

### Fine Stagione (15 Luglio - 18 Agosto)
✅ **USA:** Entrambi gli script tramite cartella `Aggiornamento_Fine_Stagione/`  
📚 **LEGGI:** `../Aggiornamento_Fine_Stagione/GUIDA_AGGIORNAMENTO.md`

---

## 🔧 Requisiti

Dipendenze necessarie (in `requirements.txt`):
```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
openpyxl>=3.1.0
pandas>=2.0.0
```

Installa con:
```bash
pip install -r scripts/requirements.txt
```

O automaticamente tramite `avvia_app.bat`

---

## 📁 File e Cartelle Correlate

**Per aggiornamenti completi fine stagione:**
- `../Aggiornamento_Fine_Stagione/` - Script e guide per cambio stagione
- `../Aggiornamento_Fine_Stagione/GUIDA_AGGIORNAMENTO.md` - Guida completa passo-passo

**Per documentazione utente:**
- `../docs/utente/QUICK_START_USER.md` - Guida rapida
- `../docs/utente/CONVERT_QUOTAZIONI_README.md` - Dettagli conversione quotazioni

**Per documentazione tecnica:**
- `../docs/sviluppo/SCALABILITY_GUIDE.md` - Come scalare l'app per nuove stagioni

---

## 💡 Note Tecniche

### convert_quotazioni.py
- Supporta fogli Excel multipli (cerca "Tutti" o "tutti")
- Gestisce header alla riga 2 (prima riga viene skippata)
- Mapping automatico nomi colonne (ID→Id, Ruolo→R, Team→Squadra, ecc.)
- Validazione ruoli (P, D, C, A)
- Output con separatore `;` per compatibilità con csv_loader.py
- Gestisce NaN e valori mancanti
- Conversione automatica tipi (Id → int, stringhe pulite)

### update_season_data.py
- Scraping da FBref.com (Serie A)
- Mapping automatico nomi squadre (FBref → App)
  - Esempio: "Internazionale" → "Inter", "AC Milan" → "Milan"
- Validazione multi-livello:
  - 20 squadre esattamente
  - 38 partite per squadra
  - Calcolo punti: Vittorie×3 + Pareggi = Punti
- Genera dizionari Python pronti all'uso
- Backup automatico file esistenti
- Preview top 10 per verifica immediata

---

## 🐛 Risoluzione Problemi

### convert_quotazioni.py

**"Foglio 'Tutti' non trovato"**
- Verifica che il file Excel scaricato contenga un foglio chiamato "Tutti" o "tutti"
- Apri il file Excel e controlla i nomi dei fogli

**"Colonne mancanti"**
- Verifica che il file contenga: Id, R/Ruolo, RM, Nome/Cognome, Squadra/Team
- Il mapping automatico dovrebbe gestire varianti comuni

**"Errore salvataggio CSV"**
- Verifica permessi scrittura cartella `data/`
- Chiudi file CSV se aperto in Excel

### update_season_data.py

**"Tabella classifica non trovata"**
- FBref potrebbe aver cambiato struttura HTML
- Verifica URL: https://fbref.com/en/comps/11/Serie-A-Stats
- Controlla che la stagione sia completata (38 giornate)

**"Validazione fallita: X squadre trovate"**
- Attendi che il campionato sia completato (38 giornate)
- Verifica che tutte le squadre abbiano giocato tutte le partite

**"Nomi squadre non corrispondono"**
- Aggiorna dizionario `team_name_mapping` nello script
- Confronta nomi in FBref vs file `data/FM_STATS_*.csv`

---

## 📊 Esempio Output update_season_data.py

```
================================================================
⚽ AGGIORNAMENTO DATI STAGIONE - SERIE A
================================================================

📦 Creazione backup...
   ✅ Backup: src/data/team_stats.py.backup.2027-07-15_143022

🔍 Scaricamento classifica da FBref...
   ✅ Scaricate 20 squadre

🧤 Scaricamento clean sheets da FBref...
   ✅ Scaricati 27 portieri

✅ Validazione classifica...
   ✅ 20 squadre, 38 partite ciascuna
   ✅ Calcolo punti verificato

================================================================
📋 PREVIEW DATI SCARICATI
================================================================

🏆 CLASSIFICA SERIE A (Top 10):
 1. Inter                -  94 pts (GF:89 GS:35)
 2. Milan                -  75 pts (GF:53 GS:35)
 3. Juventus             -  71 pts (GF:61 GS:34)
   ... e altre 17 squadre

🧤 CLEAN SHEETS PORTIERI (Top 10):
 1. Butez                -  19 CS
 2. Svilar               -  16 CS
 3. Carnesecchi          -  15 CS
   ... e altri 24 portieri

💾 Salvato: output/team_stats_2027-07-15_143022.py
✅ COMPLETATO!
```

---

## 🔗 Link Utili

- **Fantacalcio.it Quotazioni:** https://www.fantacalcio.it/quotazioni-fantacalcio
- **Fantacalcio.it Statistiche:** https://www.fantacalcio.it/statistiche-serie-a
- **FBref Serie A:** https://fbref.com/en/comps/11/Serie-A-Stats

---

**Ultimo aggiornamento:** 2026-08-09

