"""
Script per convertire file statistiche Excel da fantacalcio.it in CSV
Scarica da: https://www.fantacalcio.it/statistiche-serie-a
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


class StatisticsConverter:
    """Converte file statistiche Excel in formato CSV"""

    def __init__(self):
        self.required_columns = [
            'Id', 'R', 'Nome', 'Squadra', 'Pv', 'Mv', 'Fm',
            'Gf', 'Gs', 'Rp', 'Rc', 'Ass', 'Amm', 'Esp'
        ]

        # Mapping per normalizzare nomi colonne
        self.column_mapping = {
            'ID': 'Id',
            'id': 'Id',
            'Ruolo': 'R',
            'R.': 'R',
            'Cognome': 'Nome',
            'Team': 'Squadra',
            'Sq': 'Squadra',
            'PV': 'Pv',
            'MV': 'Mv',
            'FM': 'Fm',
            'GF': 'Gf',
            'GS': 'Gs',
            'RP': 'Rp',
            'RC': 'Rc',
            'ASS': 'Ass',
            'Ass.': 'Ass',
            'AMM': 'Amm',
            'Amm.': 'Amm',
            'ESP': 'Esp',
            'Esp.': 'Esp'
        }

    def find_excel_file(self):
        """Cerca file Excel nella cartella corrente o downloads"""
        print("\n🔍 Ricerca file Excel statistiche...")

        # Cerca in cartella corrente
        current_dir = Path('.')
        excel_files = list(current_dir.glob('*statistic*.xlsx')) + \
                     list(current_dir.glob('*statistic*.xls')) + \
                     list(current_dir.glob('*Statistic*.xlsx'))

        if excel_files:
            print(f"   ✅ Trovato: {excel_files[0].name}")
            return excel_files[0]

        # Cerca in downloads
        downloads = Path.home() / 'Downloads'
        if downloads.exists():
            excel_files = list(downloads.glob('*statistic*.xlsx')) + \
                         list(downloads.glob('*statistic*.xls'))
            if excel_files:
                latest = max(excel_files, key=lambda p: p.stat().st_mtime)
                print(f"   ✅ Trovato in Downloads: {latest.name}")
                return latest

        return None

    def normalize_column_name(self, col_name):
        """Normalizza nome colonna"""
        col_name = str(col_name).strip()

        if col_name in self.column_mapping:
            return self.column_mapping[col_name]

        return col_name

    def read_excel(self, file_path):
        """Legge file Excel statistiche"""
        print(f"\n📖 Lettura file Excel: {file_path.name}...")

        try:
            # Prova a leggere con diversi sheet
            excel_file = pd.ExcelFile(file_path)
            available_sheets = excel_file.sheet_names

            # Prova sheet comuni
            target_sheet = None
            for sheet_name in ['Tutti', 'tutti', 'Statistiche', 'statistiche', available_sheets[0]]:
                if sheet_name in available_sheets:
                    target_sheet = sheet_name
                    break

            print(f"   📄 Fogli disponibili: {available_sheets}")
            print(f"   ✅ Lettura foglio: {target_sheet}")

            # Leggi il foglio (prova con e senza skiprows)
            df = pd.read_excel(file_path, sheet_name=target_sheet, engine='openpyxl')

            # Se la prima riga sembra essere un header extra, skippa
            if df.columns[0] in ['Scarica', 'Download', 'Export']:
                print(f"   🔄 Rilevato header extra, salto prima riga...")
                df = pd.read_excel(file_path, sheet_name=target_sheet, skiprows=1, engine='openpyxl')

            print(f"   ✅ Lette {len(df)} righe")

            # Normalizza nomi colonne
            df.columns = [self.normalize_column_name(col) for col in df.columns]

            return df

        except Exception as e:
            print(f"   ❌ Errore lettura: {e}")
            return None

    def validate_columns(self, df):
        """Valida presenza colonne richieste"""
        print("\n✅ Validazione colonne...")

        missing = []
        for col in self.required_columns:
            if col not in df.columns:
                missing.append(col)

        if missing:
            print(f"   ❌ Colonne mancanti: {', '.join(missing)}")
            print(f"   📋 Colonne disponibili: {', '.join(df.columns.tolist())}")
            return False

        print(f"   ✅ Tutte le colonne richieste presenti")
        return True

    def clean_data(self, df):
        """Pulisce e valida i dati"""
        print("\n🧹 Pulizia dati...")

        # Seleziona solo le colonne necessarie
        df_clean = df[self.required_columns].copy()

        # Rimuovi righe con Id non valido
        df_clean = df_clean[df_clean['Id'].notna()]
        df_clean = df_clean[df_clean['Id'] != '']

        # Converti Id a int
        df_clean['Id'] = pd.to_numeric(df_clean['Id'], errors='coerce')
        df_clean = df_clean[df_clean['Id'].notna()]
        df_clean['Id'] = df_clean['Id'].astype(int)

        # Pulisci stringhe
        for col in ['Nome', 'Squadra', 'R']:
            df_clean[col] = df_clean[col].fillna('').astype(str).str.strip()

        # Valida ruoli
        valid_roles = ['P', 'D', 'C', 'A']
        df_clean = df_clean[df_clean['R'].isin(valid_roles)]

        # Converti colonne numeriche
        numeric_cols = ['Pv', 'Mv', 'Fm', 'Gf', 'Gs', 'Rp', 'Rc', 'Ass', 'Amm', 'Esp']
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)

        print(f"   ✅ Dati puliti: {len(df_clean)} giocatori validi")
        print(f"   📊 Portieri: {len(df_clean[df_clean['R'] == 'P'])}")
        print(f"   📊 Difensori: {len(df_clean[df_clean['R'] == 'D'])}")
        print(f"   📊 Centrocampisti: {len(df_clean[df_clean['R'] == 'C'])}")
        print(f"   📊 Attaccanti: {len(df_clean[df_clean['R'] == 'A'])}")

        return df_clean

    def save_csv(self, df, season_year):
        """Salva DataFrame come CSV"""
        output_dir = Path('../data')
        output_dir.mkdir(exist_ok=True)

        filename = f"FM_STATS_{season_year}.csv"
        full_path = output_dir / filename

        print(f"\n💾 Salvataggio CSV...")
        print(f"   📁 {full_path}")

        try:
            # Salva con punto e virgola come separatore (compatibilità app)
            df.to_csv(full_path, index=False, encoding='utf-8', sep=';')
            print(f"   ✅ Salvato con successo!")
            return full_path

        except Exception as e:
            print(f"   ❌ Errore salvataggio: {e}")
            return None

    def run(self, file_path=None, season_year=None):
        """Esegue conversione completa"""
        print("="*70)
        print("🔄 CONVERSIONE STATISTICHE SERIE A")
        print("="*70)

        # Trova file se non fornito
        if not file_path:
            file_path = self.find_excel_file()
            if not file_path:
                return None, "Nessun file Excel trovato"

        # Chiedi anno stagione se non fornito
        if not season_year:
            print("\n📅 Anno stagione (formato: 202526 per stagione 2025-26)")
            season_year = input("   Inserisci anno: ").strip()

            # Valida formato
            if len(season_year) != 6 or not season_year.isdigit():
                return None, "Formato anno non valido. Usa formato 202526"

        # Leggi Excel
        df = self.read_excel(Path(file_path))
        if df is None:
            return None, "Errore lettura file Excel"

        # Valida colonne
        if not self.validate_columns(df):
            return None, "Colonne mancanti nel file Excel"

        # Pulisci dati
        df_clean = self.clean_data(df)
        if df_clean.empty:
            return None, "Nessun dato valido trovato"

        # Salva CSV
        output_path = self.save_csv(df_clean, season_year)
        if not output_path:
            return None, "Errore salvataggio CSV"

        print("\n" + "="*70)
        print("✅ CONVERSIONE COMPLETATA!")
        print("="*70)
        print(f"\n📁 File salvato: {output_path}")
        print(f"📊 Giocatori totali: {len(df_clean)}")
        print(f"\n⚠️  IMPORTANTE:")
        print(f"   Aggiorna src/config.py con:")
        print(f"   'recent': ('FM_STATS_{season_year}.csv', 0.6)")
        print("="*70)

        return output_path, "Conversione completata con successo"


def main():
    """Funzione principale"""
    converter = StatisticsConverter()

    print("\n🎯 MODALITÀ AUTOMATICA")
    print("Cerca file Excel nella cartella corrente o Downloads\n")

    file_path = input("Premi INVIO per cercare automaticamente, o inserisci percorso file: ").strip()
    if not file_path:
        file_path = None

    converter.run(file_path=file_path)

    input("\n\nPremi INVIO per chiudere...")


if __name__ == "__main__":
    main()
