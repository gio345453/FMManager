# AGGIORNAMENTO TEAM STRENGTH

## 📊 Sistema Automatico di Calcolo Forza Squadre

Il sistema calcola automaticamente i valori di **attack**, **defense** e **overall** per tutte le squadre Serie A basandosi su **dati reali** di gol fatti/subiti delle ultime 3 stagioni.

---

## 🔄 Come Funziona

### Formula di Calcolo

1. **Statistiche Pesate** (ultime 3 stagioni):
   - Stagione più recente: **60%**
   - Stagione precedente: **30%**
   - Stagione più vecchia: **10%**

2. **Attack Rating (1-10)**:
   - Basato sui **gol fatti** pesati
   - Più gol = rating più alto
   - Normalizzato su scala 1-10

3. **Defense Rating (1-10)**:
   - Basato sui **gol subiti** pesati
   - **Meno gol subiti = rating più alto** (scala invertita)
   - Normalizzato su scala 1-10

4. **Overall Rating**:
   - Media di Attack e Defense
   - `Overall = (Attack + Defense) / 2`

---

## 🎯 Scalabilità Automatica

Lo script è **completamente scalabile**:

```python
# Rileva automaticamente le ultime 3 stagioni in base alla data corrente
# Esempio: Agosto 2026 → [2026-27, 2025-26, 2024-25]
# Esempio: Agosto 2027 → [2027-28, 2026-27, 2025-26]
```

**Non serve modificare il codice** ogni anno! Lo script calcola automaticamente:
- Quale stagione è quella corrente (basandosi su mese/anno)
- Quali sono le 3 stagioni da usare
- I pesi da applicare (sempre 60%, 30%, 10%)

---

## 📁 File Coinvolti

### Input
- `Aggiornamento_Fine_Stagione/team_stats_fbref.json`
  - Contiene gol fatti/subiti di tutte le squadre per 3 stagioni
  - Formato: `{gf, gs, punti, partite}` per ogni squadra/stagione
  - **AGGIORNAMENTO MANUALE**: ogni fine stagione inserisci i dati reali

### Output
- `data/Calendario/team_strength.json`
  - Valori finali di attack/defense/overall (1-10)
  - Usato dall'app per calcolare difficoltà avversari
  - Ordinato per overall rating decrescente

### Script
- `Aggiornamento_Fine_Stagione/calculate_team_strength.py`
  - Legge `team_stats_fbref.json`
  - Calcola statistiche pesate
  - Normalizza su scala 1-10
  - Genera `team_strength.json`

---

## 🚀 Esecuzione

### Opzione 1: Automatico (consigliato)
Esegui il bat di fine stagione:
```batch
Aggiornamento_Fine_Stagione\Premere_15_luglio_o_dopo.bat
```

Il bat esegue automaticamente:
1. Download classifica Serie A
2. Download clean sheets
3. **Calcolo team strength** ← NUOVO!
4. Download calendario
5. Validazione dati

### Opzione 2: Manuale
Esegui direttamente lo script:
```batch
python Aggiornamento_Fine_Stagione\calculate_team_strength.py
```

---

## 📝 Procedura Annuale

### 1. Fine Stagione (Luglio)
Aggiorna `team_stats_fbref.json` con i dati reali della stagione appena conclusa:

```json
{
  "2026-27": {
    "Inter": {"gf": 85, "gs": 28, "punti": 88, "partite": 38},
    "Napoli": {"gf": 78, "gs": 35, "punti": 82, "partite": 38},
    ...
  },
  "2025-26": { ... },
  "2024-25": { ... }
}
```

Fonti dati:
- [FBref Serie A](https://fbref.com/en/comps/11/Serie-A-Stats)
- [Transfermarkt](https://www.transfermarkt.it/)
- Sito ufficiale Lega Serie A

### 2. Esegui il Calcolo
```batch
python Aggiornamento_Fine_Stagione\calculate_team_strength.py
```

### 3. Verifica Output
Lo script mostra:
- Stagioni rilevate automaticamente
- Statistiche pesate per ogni squadra
- Rating finali (attack/defense/overall)
- Top 5 per categoria

### 4. File Aggiornato
`data/Calendario/team_strength.json` è ora aggiornato con i nuovi valori!

---

## 📊 Esempio Output

```
================================================================================
GENERAZIONE team_strength.json DA DATI REALI
================================================================================

📅 Stagioni rilevate automaticamente:
   • 2026-27: 60%
   • 2025-26: 30%
   • 2024-25: 10%

--------------------------------------------------------------------------------
Squadra          GF Pesati  GS Pesati   Attack  Defense  Overall
--------------------------------------------------------------------------------
Inter                 89.0       22.0      9.6      9.8      9.7
Atalanta              91.5       42.0     10.0      6.2      8.1
Juventus              54.0       20.8      3.9     10.0      7.0
...
```

---

## ⚠️ Note Importanti

1. **Squadre Nuove/Retrocesse**:
   - Se una squadra non ha dati per tutte e 3 le stagioni, lo script normalizza automaticamente i pesi
   - Squadre senza alcun dato ricevono valori medi (5.5)

2. **Stagione In Corso**:
   - Stagioni con `partite: 0` vengono automaticamente ignorate
   - Utile quando aggiorni il file a inizio stagione

3. **Precisione**:
   - Valori arrotondati a 1 decimale
   - Normalizzazione garantisce sempre range 1.0-10.0

4. **Backup**:
   - Prima di eseguire, fai sempre backup di `team_strength.json`
   - Il bat di fine stagione lo fa automaticamente

---

## 🔧 Manutenzione

### Se una squadra ha nome diverso
Aggiorna il mapping in `calculate_team_strength.py`:

```python
self.team_mapping = {
    'Hellas Verona': 'Verona',
    'AC Milan': 'Milan',
    ...
}
```

### Se cambia la formula
Modifica i pesi in `_get_last_3_seasons()` e `__init__()`:

```python
self.weights = {
    self.seasons[0]: 0.60,  # Stagione più recente
    self.seasons[1]: 0.30,  # Stagione media
    self.seasons[2]: 0.10   # Stagione più vecchia
}
```

---

## ✅ Vantaggi del Sistema

1. **Automatico**: calcolo basato su dati reali, non stime manuali
2. **Scalabile**: rileva automaticamente le stagioni da usare ogni anno
3. **Trasparente**: formula chiara e verificabile
4. **Consistente**: stessi criteri per tutte le squadre
5. **Integrato**: parte del processo di aggiornamento fine stagione

---

## 📚 Riferimenti

- Formula originale: `team_coefficients.md`
- Dati input: `team_stats_fbref.json`
- Output: `data/Calendario/team_strength.json`
- Script: `calculate_team_strength.py`
- Bat automazione: `Premere_15_luglio_o_dopo.bat`
