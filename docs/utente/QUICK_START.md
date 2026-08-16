# 🚀 Quick Start - Aggiornamento Dati Stagione

Guida veloce per aggiornare i dati ogni anno.

---

## ⚡ Procedura Rapida (5 minuti)

### **STEP 1: Installa dipendenze** (solo prima volta)

```bash
cd scripts
pip install -r requirements.txt
```

### **STEP 2: Esegui lo script**

```bash
python update_season_data.py
```

### **STEP 3: Controlla output**

Lo script mostra preview e salva i file in `scripts/output/`

### **STEP 4: Copia nei file originali**

1. Apri `scripts/output/team_stats_generated_*.py`
2. Copia il dizionario `CLASSIFICA_REALE_CURRENT_SEASON`
3. Incolla in `src/data/team_stats.py` (sostituisci il vecchio)

4. Apri `scripts/output/clean_sheets_generated_*.py`
5. Copia il dizionario `CLEAN_SHEETS_CURRENT_SEASON`
6. Incolla in `src/data/clean_sheets_data.py` (sostituisci il vecchio)

### **STEP 5: Testa**

```bash
python main_modern.py
```

Verifica che dashboard squadre mostri l'anno corretto.

---

## 🎯 Checklist Veloce

```
□ Script eseguito senza errori?
□ Preview dati corretta?
□ 20 squadre nella classifica?
□ Almeno 15 portieri nei clean sheets?
□ Nomi squadre corretti?
□ File copiati nei file originali?
□ App testata e funzionante?
```

---

## ⚠️ Se qualcosa non funziona

1. **Leggi `scripts/README.md`** - Documentazione completa
2. **Controlla backup** - File `.backup.*` in `src/data/`
3. **Controlla errori** - Output dello script
4. **Aggiorna manualmente** - Se necessario

---

## 📞 Supporto

- Documentazione completa: `scripts/README.md`
- Guida scalabilità: `SCALABILITY_GUIDE.md`
- Report modifiche: `SCALABILITY_CHANGES_REPORT.md`
