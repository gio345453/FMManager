# Download Calendario Serie A

FBref blocca lo scraping automatico. Usa questo processo manuale:

## Processo

### 1. Scarica CSV da FBref

1. Vai su https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures
2. Clicca su **"Share & Export"** (sotto la tabella)
3. Seleziona **"Get table as CSV (for Excel)"**
4. Copia il testo CSV
5. Salva come `data/Calendario/calendario_raw.csv`

### 2. Converti in JSON

```bash
python scripts/convert_calendario_csv.py --season 2024-25
```

Il file verrà salvato come `data/Calendario/calendario.json`

## Formato Output

```json
{
  "season": "2024-25",
  "download_date": "2026-08-27T...",
  "source": "CSV Manual Import",
  "total_matches": 380,
  "matches": [
    {
      "matchday": 1,
      "date": "2024-08-17",
      "home_team": "Genoa",
      "away_team": "Inter",
      "home_goals": 2,
      "away_goals": 2,
      "played": true
    },
    ...
  ]
}
```

## Note

- Il calendario viene usato da `fixture_difficulty.py` per calcolare la difficoltà delle partite
- Per la rotazione portieri serve solo il matchup casa/trasferta (i risultati sono opzionali)
- Lo script normalizza automaticamente i nomi delle squadre
