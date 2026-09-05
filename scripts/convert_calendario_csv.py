"""
Converte calendario Serie A da CSV (scaricato manualmente) a JSON

Come ottenere il CSV:
1. Vai su https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures
2. Clicca "Share & Export" → "Get table as CSV (for Excel)"
3. Salva come data/Calendario/calendario_raw.csv
4. Esegui: python scripts/convert_calendario_csv.py

Alternativamente usa il CSV della Lega Serie A dal loro sito
"""
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import argparse


class CalendarioCSVConverter:
    """Converte calendario CSV in formato JSON standard"""

    def __init__(self, csv_file, season='2024-25'):
        self.csv_file = Path(csv_file)
        self.season = season
        self.output_dir = Path('data/Calendario')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Mappa nomi squadre
        self.team_mapping = {
            'Atalanta': 'Atalanta',
            'Bologna': 'Bologna',
            'Cagliari': 'Cagliari',
            'Como': 'Como',
            'Empoli': 'Empoli',
            'Fiorentina': 'Fiorentina',
            'Genoa': 'Genoa',
            'Inter': 'Inter',
            'Juventus': 'Juventus',
            'Lazio': 'Lazio',
            'Lecce': 'Lecce',
            'Milan': 'Milan',
            'Monza': 'Monza',
            'Napoli': 'Napoli',
            'Parma': 'Parma',
            'Roma': 'Roma',
            'Torino': 'Torino',
            'Udinese': 'Udinese',
            'Venezia': 'Venezia',
            'Verona': 'Verona',
            # Varianti
            'Hellas Verona': 'Verona',
            'AC Milan': 'Milan',
            'Inter Milan': 'Inter',
            'AS Roma': 'Roma'
        }

    def normalize_team_name(self, name):
        """Normalizza nome squadra"""
        name = str(name).strip()
        return self.team_mapping.get(name, name)

    def convert(self):
        """Converte CSV in JSON"""
        print("="*70)
        print("CONVERSIONE CALENDARIO CSV → JSON")
        print("="*70)
        print(f"\nFile CSV: {self.csv_file}")
        print(f"Stagione: {self.season}")

        if not self.csv_file.exists():
            print(f"\n❌ File non trovato: {self.csv_file}")
            print("\nCome scaricare il CSV:")
            print("1. Vai su https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures")
            print("2. Clicca 'Share & Export' → 'Get table as CSV'")
            print("3. Salva come data/Calendario/calendario_raw.csv")
            return None

        try:
            print("\n📂 Lettura CSV...")
            # Prova diversi separatori e encoding
            try:
                df = pd.read_csv(self.csv_file, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(self.csv_file, encoding='latin1')
                except:
                    df = pd.read_csv(self.csv_file, sep=';', encoding='utf-8')

            print(f"✅ Righe lette: {len(df)}")
            print(f"   Colonne: {', '.join(df.columns.tolist())}")

            # Parse calendario
            print("\n🔍 Parsing partite...")
            matches = self._parse_dataframe(df)

            if not matches:
                print("❌ Nessuna partita valida trovata")
                return None

            print(f"✅ Partite parsate: {len(matches)}")

            # Salva
            output = {
                'season': self.season,
                'download_date': datetime.now().isoformat(),
                'source': 'CSV Manual Import',
                'total_matches': len(matches),
                'matches': matches
            }

            output_file = self.output_dir / 'calendario.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Calendario salvato: {output_file}")

            self._print_summary(matches)

            return output

        except Exception as e:
            print(f"\n❌ Errore: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_dataframe(self, df):
        """Parse DataFrame in formato matches"""
        matches = []

        # Rileva colonne (FBref usa nomi inglesi)
        col_map = self._detect_columns(df)

        if not all([col_map.get('home'), col_map.get('away')]):
            print("⚠️  Impossibile rilevare colonne home/away")
            print(f"   Colonne disponibili: {df.columns.tolist()}")
            return []

        for idx, row in df.iterrows():
            try:
                # Giornata
                matchday = row.get(col_map.get('matchday', 'Wk'), idx // 10 + 1)
                if pd.isna(matchday):
                    matchday = idx // 10 + 1
                else:
                    try:
                        matchday = int(matchday)
                    except:
                        matchday = idx // 10 + 1

                # Data
                date = row.get(col_map.get('date', 'Date'), '')
                if pd.notna(date):
                    date = str(date)[:10]  # Solo YYYY-MM-DD
                else:
                    date = None

                # Squadre
                home_team = self.normalize_team_name(row[col_map['home']])
                away_team = self.normalize_team_name(row[col_map['away']])

                if not home_team or not away_team:
                    continue

                # Risultato
                score_col = col_map.get('score', 'Score')
                score = row.get(score_col, '')
                home_goals = None
                away_goals = None
                played = False

                if pd.notna(score) and str(score).strip():
                    score_str = str(score).strip()
                    # FBref usa "–" (en dash)
                    if '–' in score_str:
                        parts = score_str.split('–')
                    elif '-' in score_str:
                        parts = score_str.split('-')
                    else:
                        parts = []

                    if len(parts) == 2:
                        try:
                            home_goals = int(parts[0].strip())
                            away_goals = int(parts[1].strip())
                            played = True
                        except:
                            pass

                matches.append({
                    'matchday': matchday,
                    'date': date,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'played': played
                })

            except Exception as e:
                print(f"⚠️  Errore riga {idx}: {e}")
                continue

        return matches

    def _detect_columns(self, df):
        """Rileva nomi colonne (supporta vari formati)"""
        col_map = {}

        cols_lower = {col.lower(): col for col in df.columns}

        # Giornata
        for key in ['wk', 'week', 'round', 'giornata', 'matchday']:
            if key in cols_lower:
                col_map['matchday'] = cols_lower[key]
                break

        # Data
        for key in ['date', 'data']:
            if key in cols_lower:
                col_map['date'] = cols_lower[key]
                break

        # Casa
        for key in ['home', 'home team', 'casa', 'squadra casa']:
            if key in cols_lower:
                col_map['home'] = cols_lower[key]
                break

        # Trasferta
        for key in ['away', 'away team', 'trasferta', 'squadra trasferta']:
            if key in cols_lower:
                col_map['away'] = cols_lower[key]
                break

        # Risultato
        for key in ['score', 'result', 'risultato']:
            if key in cols_lower:
                col_map['score'] = cols_lower[key]
                break

        return col_map

    def _print_summary(self, matches):
        """Stampa riepilogo"""
        print("\n" + "="*70)
        print("RIEPILOGO CALENDARIO")
        print("="*70)

        matchdays = set(m['matchday'] for m in matches)
        print(f"\n📅 Giornate: {len(matchdays)} (da {min(matchdays)} a {max(matchdays)})")

        teams = set()
        for m in matches:
            teams.add(m['home_team'])
            teams.add(m['away_team'])
        print(f"⚽ Squadre: {len(teams)}")
        print(f"   {', '.join(sorted(teams))}")

        played = sum(1 for m in matches if m['played'])
        to_play = len(matches) - played
        print(f"\n✅ Partite giocate: {played}")
        print(f"⏳ Partite da giocare: {to_play}")

        print(f"\n📋 Prime 5 partite:")
        for m in matches[:5]:
            status = "✓" if m['played'] else "○"
            if m['played']:
                score = f"{m['home_goals']}-{m['away_goals']}"
            else:
                score = "vs"
            print(f"   {status} G{m['matchday']:2} | {m['home_team']:15} {score:5} {m['away_team']:15} | {m['date']}")

        print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description='Converte calendario CSV in JSON')
    parser.add_argument('--csv', default='data/Calendario/calendario_raw.csv',
                       help='File CSV da convertire')
    parser.add_argument('--season', default='2024-25',
                       help='Stagione (formato: 2024-25)')
    args = parser.parse_args()

    converter = CalendarioCSVConverter(csv_file=args.csv, season=args.season)
    result = converter.convert()

    if result:
        print("\n✅ Conversione completata!")
    else:
        print("\n❌ Conversione fallita")


if __name__ == "__main__":
    main()
