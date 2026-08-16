# 📥 Script Conversione Quotazioni Fantacalcio.it

Converte il file Excel delle quotazioni in formato CSV per l'applicazione.

---

## 🎯 **QUANDO USARE**

**Prima di ogni nuova stagione** (es. inizio stagione 2027-28)

---

## 🚀 **DUE MODI PER USARLO**

### **METODO 1: Dalla UI dell'App** ⭐ PIÙ FACILE

1. **Avvia l'applicazione:**
   ```bash
   python main_modern.py
   ```

2. **Clicca sul pulsante:**
   ```
   📥 Scarica ultimo listone disponibile
   ```
   (Si trova in alto a destra, vicino a "Lista Giocatori")

3. **Seleziona il file Excel** scaricato da fantacalcio.it

4. **Attendi conversione** (5-10 secondi)

5. **FATTO!** Il file CSV è stato salvato in `data/`

---

### **METODO 2: Script Standalone**

1. **Scarica Excel da fantacalcio.it:**
   - Vai su https://www.fantacalcio.it/quotazioni-fantacalcio
   - Clicca su "Scarica quotazioni" o "Export Excel"
   - Salva il file (es. in Downloads)

2. **Esegui lo script:**
   ```bash
   python scripts/convert_quotazioni.py
   ```

3. **Seleziona il file:**
   - Inserisci il path completo, oppure
   - Lascia vuoto per ricerca automatica

4. **Verifica preview** e conferma

5. **FATTO!** File salvato come `CURRENT_SEASON_*.csv` in `data/`

---

## 📋 **COSA FA LO SCRIPT**

### **Automatico:**
✅ Legge file Excel  
✅ Trova colonne: Id, R, RM, Nome, Squadra  
✅ Pulisce dati (spazi, encoding, NaN)  
✅ Valida ruoli (P, D, C, A)  
✅ Rimuove righe non valide  
✅ Converte in formato CSV UTF-8  
✅ Salva come `CURRENT_SEASON_YYYY_YYYY.csv`  

---

## 🔍 **COLONNE RICHIESTE NEL FILE EXCEL**

Il file Excel deve contenere queste colonne (nomi possono variare):

| Colonna App | Possibili Nomi Excel |
|-------------|---------------------|
| **Id** | ID, id, Id |
| **R** | Ruolo, R., R |
| **RM** | Ruoli Mantra, RM, Rm |
| **Nome** | Cognome, Giocatore, Nome |
| **Squadra** | Team, Club, Squadra |

Lo script riconosce automaticamente le variazioni.

---

## 📊 **ESEMPIO OUTPUT**

```
════════════════════════════════════════════════════════════════
📥 CONVERSIONE QUOTAZIONI FANTACALCIO.IT
════════════════════════════════════════════════════════════════

🔍 Ricerca file Excel...
   ✅ Trovato in Downloads: Quotazioni_2027.xlsx

📖 Lettura file Excel: Quotazioni_2027.xlsx...
   ✅ Lette 623 righe

✅ Validazione colonne...
   ✅ Tutte le colonne presenti

🧹 Pulizia dati...
   ✅ Dati puliti: 623 giocatori validi

════════════════════════════════════════════════════════════════
📋 PREVIEW QUOTAZIONI
════════════════════════════════════════════════════════════════

 Id  Nome              Squadra        R   RM
  1  Maignan           Milan          P   
  2  Di Gregorio       Juventus       P   
  3  Bastoni           Inter          D   
  4  Theo Hernandez    Milan          D   E
  5  Calhanoglu        Inter          C   T

Totale giocatori: 623

📊 Distribuzione per ruolo:
   P: 68 giocatori
   D: 187 giocatori
   C: 223 giocatori
   A: 145 giocatori

💾 Salvare come CSV? [S]ì / [N]o: S

💾 Salvataggio CSV...
   📁 data/CURRENT_SEASON_2027_2028.csv
   ✅ Salvato con successo!

════════════════════════════════════════════════════════════════
✅ CONVERSIONE COMPLETATA!
════════════════════════════════════════════════════════════════

File salvato: data\CURRENT_SEASON_2027_2028.csv

📝 PROSSIMI PASSI:
   1. Aggiorna src/config.py con il nuovo nome file
   2. Esegui Premere_15_luglio_o_dopo.bat
```

---

## ⚙️ **PROSSIMI PASSI DOPO CONVERSIONE**

### **1. Aggiorna config.py:**

```python
# src/config.py
CURRENT_SEASON_FILE = "CURRENT_SEASON_2027_2028.csv"  # ← Il nuovo file
```

### **2. Verifica il file:**

```bash
# Apri data/CURRENT_SEASON_2027_2028.csv
# Controlla che ci siano tutti i giocatori
```

### **3. Riavvia l'app:**

```bash
python main_modern.py
```

---

## 🔧 **GESTIONE COLONNE VARIABILI**

Se fantacalcio.it cambia nomi delle colonne, aggiorna il mapping in `convert_quotazioni.py`:

```python
self.column_mapping = {
    'ID': 'Id',
    'id': 'Id',
    'Ruolo': 'R',
    # ... aggiungi nuovi mapping qui
}
```

---

## ⚠️ **RISOLUZIONE PROBLEMI**

### **Problema: "Colonne richieste mancanti"**

**Causa:** File Excel non ha le colonne corrette  
**Soluzione:**
1. Apri Excel manualmente
2. Verifica colonne presenti
3. Rinomina se necessario: Id, R, RM, Nome, Squadra
4. Salva e riprova

### **Problema: "Errore lettura file Excel"**

**Causa:** File corrotto o formato non supportato  
**Soluzione:**
1. Riscarica file da fantacalcio.it
2. Verifica che sia .xlsx o .xls
3. Prova ad aprire con Excel per verificare

### **Problema: "openpyxl not found"**

**Causa:** Dipendenza mancante  
**Soluzione:**
```bash
pip install openpyxl pandas
```

### **Problema: "Encoding errato (caratteri strani)"**

**Causa:** File non UTF-8  
**Soluzione:** Lo script gestisce automaticamente, ma se persiste:
1. Apri Excel
2. Salva come → CSV UTF-8
3. Usa quello invece dell'xlsx

---

## 📚 **FILE CORRELATI**

- `scripts/update_season_data.py` - Aggiorna classifica e clean sheets
- `Premere_15_luglio_o_dopo.bat` - Script completo aggiornamento
- `SCALABILITY_GUIDE.md` - Guida aggiornamento stagioni

---

## ✅ **CHECKLIST**

Prima di ogni nuova stagione:

- [ ] Scaricato file Excel da fantacalcio.it
- [ ] Eseguito conversione (UI o script)
- [ ] File CSV salvato in data/
- [ ] Aggiornato CURRENT_SEASON_FILE in config.py
- [ ] Testato che app carichi i nuovi giocatori

---

**Tempo totale:** ~2 minuti ⚡  
**Difficoltà:** 🟢 Facile
