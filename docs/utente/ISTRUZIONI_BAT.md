# 🎯 ISTRUZIONI FILE .BAT - Aggiornamento Automatico

---

## 📅 **QUANDO USARE**

**Data:** 15 Luglio (o dopo) di ogni anno  
**File:** `Premere_15_luglio_o_dopo.bat`

---

## 🚀 **COME USARE**

### **STEP 1: Doppio click sul file**

```
📁 FantaCalcio-App/
├── Premere_15_luglio_o_dopo.bat  ← DOPPIO CLICK QUI
```

### **STEP 2: Lo script fa tutto automaticamente**

```
✅ Verifica Python installato
✅ Installa dipendenze (se mancano)
✅ Crea backup automatico
✅ Scarica dati da FBref
✅ Valida i dati
✅ Genera codice Python
✅ Salva in scripts/output/
```

### **STEP 3: Copia i file generati (2 minuti)**

Il .bat ti dice esattamente cosa fare:

1. **Apri** `scripts/output/team_stats_generated_*.py`
2. **Copia** il dizionario `CLASSIFICA_REALE_CURRENT_SEASON`
3. **Incolla** in `src/data/team_stats.py` (sostituisci il vecchio)

4. **Apri** `scripts/output/clean_sheets_generated_*.py`
5. **Copia** il dizionario `CLEAN_SHEETS_CURRENT_SEASON`
6. **Incolla** in `src/data/clean_sheets_data.py` (sostituisci il vecchio)

### **STEP 4: Testa**

```bash
python main_modern.py
```

---

## ✅ **COSA FA IL .BAT**

| Fase | Azione | Tempo |
|------|--------|-------|
| 1️⃣ | Verifica posizione corretta | 1 sec |
| 2️⃣ | Mostra istruzioni | Lettura |
| 3️⃣ | Verifica Python installato | 2 sec |
| 4️⃣ | Installa dipendenze (se mancano) | 10-30 sec |
| 5️⃣ | Esegue script Python | 20-30 sec |
| 6️⃣ | Mostra risultati e istruzioni | Lettura |
| 7️⃣ | Opzione: apri cartella output | Click |

**Tempo totale:** ~1-2 minuti (automatico)

---

## 🎨 **SCREENSHOT ESEMPIO OUTPUT**

```
════════════════════════════════════════════════════════════════
    ⚽ AGGIORNAMENTO DATI STAGIONE SERIE A
════════════════════════════════════════════════════════════════

    📅 QUANDO ESEGUIRE: 15 Luglio (o dopo)
    ⏱️  TEMPO RICHIESTO: ~5 minuti

════════════════════════════════════════════════════════════════

✅ Python trovato: Python 3.11.0
✅ Dipendenze già installate

════════════════════════════════════════════════════════════════
    🚀 AVVIO SCRIPT
════════════════════════════════════════════════════════════════

📦 Creazione backup...
   ✅ Backup: src/data/team_stats.py.backup.2027-07-15_143022

🔍 Scaricamento classifica da FBref...
   ✅ Scaricate 20 squadre

🧤 Scaricamento clean sheets da FBref...
   ✅ Scaricati 27 portieri

✅ Validazione classifica...
   ✅ Validazione OK!

📋 PREVIEW DATI SCARICATI
🏆 CLASSIFICA SERIE A (Top 10):
 1. Inter                -  94 pts
 2. Milan                -  75 pts
 ...

💾 Salvato: scripts/output/team_stats_generated_2027-07-15.py
💾 Salvato: scripts/output/clean_sheets_generated_2027-07-15.py

════════════════════════════════════════════════════════════════
    ✅ COMPLETATO!
════════════════════════════════════════════════════════════════

📝 PROSSIMI PASSI:
   1. Apri la cartella: scripts\output\
   2. Copia il contenuto...
   3. Verifica i nomi delle squadre
   4. Testa l'applicazione

Vuoi aprire la cartella output? [S/N]
```

---

## ⚠️ **RISOLUZIONE PROBLEMI**

### **Problema: "Python non trovato"**

**Soluzione:**
1. Installa Python: https://www.python.org/downloads/
2. Durante installazione: ✅ Spunta "Add Python to PATH"
3. Riavvia PC
4. Riesegui .bat

### **Problema: "Dipendenze mancanti"**

**Soluzione:**
Il .bat le installa automaticamente. Se fallisce:
```bash
pip install -r scripts/requirements.txt
```

### **Problema: "FBref non raggiungibile"**

**Soluzione:**
1. Controlla connessione internet
2. Aspetta 5-10 minuti
3. Riprova
4. Se persiste → aggiornamento manuale (vedi SCALABILITY_GUIDE.md)

### **Problema: "File non trovato"**

**Soluzione:**
- Assicurati di eseguire `Premere_15_luglio_o_dopo.bat` dalla **cartella principale** del progetto
- Non dalla cartella `scripts/`

---

## 🔄 **FLUSSO COMPLETO**

```
[Doppio click .bat]
       ↓
[Verifica Python] ✅
       ↓
[Installa dipendenze] ✅
       ↓
[Backup automatico] ✅
       ↓
[Download FBref] ✅
       ↓
[Validazione] ✅
       ↓
[Generazione codice] ✅
       ↓
[Salvataggio output] ✅
       ↓
[Istruzioni prossimi passi] 📝
       ↓
[Apri cartella output] 📁
       ↓
[Tu: copia-incolla] ✏️ (2 min)
       ↓
[Test app] 🚀
       ↓
[FATTO] ✅
```

---

## 💡 **SUGGERIMENTI**

### **Prima volta:**
- ✅ Leggi attentamente ogni messaggio
- ✅ Non chiudere la finestra prematuramente
- ✅ Verifica i file generati prima di copiare

### **Anni successivi:**
- ⚡ Processo velocissimo (già tutto configurato)
- ⚡ Solo doppio click + copia-incolla
- ⚡ 3-5 minuti totali

---

## 📚 **DOCUMENTAZIONE CORRELATA**

- `SCALABILITY_GUIDE.md` - Guida completa aggiornamento
- `scripts/README.md` - Documentazione script dettagliata
- `scripts/QUICK_START.md` - Guida rapida

---

## ✅ **CHECKLIST VELOCE**

Quando esegui il .bat:

- [ ] Python installato?
- [ ] Connessione internet attiva?
- [ ] File .bat eseguito da cartella principale?
- [ ] Backup creato?
- [ ] Dati scaricati?
- [ ] File generati in scripts/output/?
- [ ] Preview verificata?
- [ ] Codice copiato nei file originali?
- [ ] App testata?

---

**💚 Pronto per il 15 luglio 2027!**
