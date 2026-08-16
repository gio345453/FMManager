"""
Script per Conversione Quotazioni Fantacalcio.it
Converte file Excel quotazioni in formato CSV per l'app

Esecuzione: python scripts/convert_quotazioni.py
"""

import pandas as pd
import sys
import re
from pathlib import Path
from datetime import datetime


class QuotazioniConverter:
    """Converte file Excel quotazioni in CSV formato app"""

    def __init__(self):
        # Mapping colonne Excel → App (gestisce variazioni nomi)
        self.column_mapping = {
            'ID': 'Id',
            'id': 'Id',
            'Id': 'Id',
            'Ruolo': 'R',
            'R.': 'R',
            'R': 'R',
            'Ruoli Mantra': 'RM',
            'RM': 'RM',
            'Rm': 'RM',
            'Cognome': 'Nome',
            'Giocatore': 'Nome',
            'Nome': 'Nome',
            'Team': 'Squadra',
            'Club': 'Squadra',
            'Squadra': 'Squadra'
        }

        # Colonne richieste nell'output
        self.required_columns = ['Id', 'R', 'RM', 'Nome', 'Squadra']

    def find_excel_file(self):
        """Cerca file Excel nella cartella corrente o downloads"""
        print("\n🔍 Ricerca file Excel...")

        # Cerca in cartella corrente
        current_dir = Path('.')
        excel_files = list(current_dir.glob('*.xlsx')) + list(current_dir.glob('*.xls'))

        if excel_files:
            print(f"   ✅ Trovato: {excel_files[0].name}")
            return excel_files[0]

        # Cerca in downloads
        downloads = Path.home() / 'Downloads'
        if downloads.exists():
            excel_files = list(downloads.glob('*.xlsx')) + list(downloads.glob('*.xls'))
            if excel_files:
                # Prendi il più recente
                latest = max(excel_files, key=lambda p: p.stat().st_mtime)
                print(f"   ✅ Trovato in Downloads: {latest.name}")
                return latest

        return None

    def normalize_column_name(self, col_name):
        """Normalizza nome colonna"""
        # Rimuovi spazi extra
        col_name = str(col_name).strip()

        # Usa mapping se presente
        if col_name in self.column_mapping:
            return self.column_mapping[col_name]

        return col_name

    def read_excel(self, file_path):
        """Legge file Excel e identifica colonne"""
        print(f"\n📖 Lettura file Excel: {file_path.name}...")

        try:
            # Leggi foglio "Tutti", salta prima riga (header alla riga 2)
            try:
                df = pd.read_excel(file_path, sheet_name='Tutti', skiprows=1, engine='openpyxl')
                print(f"   ✅ Letto foglio 'Tutti' (saltata prima riga)")
            except ValueError:
                # Prova con "tutti" minuscolo
                try:
                    df = pd.read_excel(file_path, sheet_name='tutti', skiprows=1, engine='openpyxl')
                    print(f"   ✅ Letto foglio 'tutti' (saltata prima riga)")
                except ValueError:
                    # Mostra fogli disponibili
                    excel_file = pd.ExcelFile(file_path)
                    available_sheets = excel_file.sheet_names
                    print(f"   ❌ Foglio 'Tutti' non trovato. Fogli disponibili: {available_sheets}")
                    return None

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
            print(f"   📋 Colonne trovate: {', '.join(df.columns)}")
            return False

        print(f"   ✅ Tutte le colonne presenti")
        return True

    def clean_data(self, df):
        """Pulisce e normalizza dati"""
        print("\n🧹 Pulizia dati...")

        # Seleziona solo colonne necessarie
        df_clean = df[self.required_columns].copy()

        # Rimuovi righe con Id vuoto
        df_clean = df_clean[df_clean['Id'].notna()]

        # Converti Id in int
        df_clean['Id'] = pd.to_numeric(df_clean['Id'], errors='coerce').astype('Int64')

        # Rimuovi righe con Id non valido
        df_clean = df_clean[df_clean['Id'].notna()]

        # Pulisci RM (gestisci NaN)
        df_clean['RM'] = df_clean['RM'].fillna('')
        df_clean['RM'] = df_clean['RM'].astype(str).str.strip()
        df_clean['RM'] = df_clean['RM'].replace('nan', '')
        df_clean['RM'] = df_clean['RM'].replace('NaN', '')

        # Pulisci nomi (rimuovi spazi extra)
        df_clean['Nome'] = df_clean['Nome'].str.strip()
        df_clean['Squadra'] = df_clean['Squadra'].str.strip()
        df_clean['R'] = df_clean['R'].str.strip()

        # Valida ruoli
        valid_roles = ['P', 'D', 'C', 'A']
        invalid_roles = ~df_clean['R'].isin(valid_roles)
        if invalid_roles.any():
            print(f"   ⚠️  {invalid_roles.sum()} giocatori con ruolo non valido (rimossi)")
            df_clean = df_clean[~invalid_roles]

        print(f"   ✅ Dati puliti: {len(df_clean)} giocatori validi")

        return df_clean

    def show_preview(self, df):
        """Mostra preview dati"""
        print("\n" + "="*70)
        print("📋 PREVIEW QUOTAZIONI")
        print("="*70)
        print()
        print(df.head(15).to_string(index=False))
        print()
        print(f"... e altri {len(df) - 15} giocatori" if len(df) > 15 else "")
        print()
        print("="*70)
        print(f"Totale giocatori: {len(df)}")

        # Statistiche per ruolo
        print("\n📊 Distribuzione per ruolo:")
        for role in ['P', 'D', 'C', 'A']:
            count = len(df[df['R'] == role])
            print(f"   {role}: {count} giocatori")

        print("="*70)

    def detect_season_year(self):
        """Rileva anno stagione corrente"""
        now = datetime.now()
        year = now.year

        # Se siamo dopo giugno, la nuova stagione è anno+1
        if now.month >= 6:
            return f"{year}_{year+1}"
        else:
            return f"{year-1}_{year}"

    def save_csv(self, df, output_dir='data'):
        """Salva DataFrame come CSV"""
        # Crea cartella se non esiste
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Genera nome file
        season_year = self.detect_season_year()
        filename = f"CURRENT_SEASON_{season_year}.csv"
        full_path = output_path / filename

        print(f"\n💾 Salvataggio CSV...")
        print(f"   📁 {full_path}")

        try:
            # Salva come CSV (UTF-8, punto e virgola come separatore per compatibilità)
            df.to_csv(full_path, index=False, encoding='utf-8', sep=';')
            print(f"   ✅ Salvato con successo!")
            return full_path

        except Exception as e:
            print(f"   ❌ Errore salvataggio: {e}")
            return None

    def run_interactive(self):
        """Esecuzione interattiva"""
        print("\n" + "="*70)
        print("📥 CONVERSIONE QUOTAZIONI FANTACALCIO.IT")
        print("="*70)
        print()
        print("Questo script converte il file Excel delle quotazioni")
        print("in formato CSV per l'applicazione FantaCalcio Manager.")
        print()
        print("="*70)

        # Step 1: Ottieni path file
        print("\n📂 Seleziona file Excel:")
        print("   1. Inserisci path completo")
        print("   2. Lascia vuoto per cercare automaticamente")
        print()

        user_input = input("Path file Excel (o Invio per ricerca auto): ").strip()

        if user_input:
            file_path = Path(user_input)
            if not file_path.exists():
                print(f"\n❌ File non trovato: {file_path}")
                return
        else:
            file_path = self.find_excel_file()
            if not file_path:
                print("\n❌ Nessun file Excel trovato!")
                print("\nScarica il file da:")
                print("   https://www.fantacalcio.it/quotazioni-fantacalcio")
                print("\nPoi riesegui questo script.")
                return

        # Step 2: Leggi Excel
        df = self.read_excel(file_path)
        if df is None:
            return

        # Step 3: Valida colonne
        if not self.validate_columns(df):
            print("\n❌ Struttura file non valida!")
            print("\nVerifica che il file contenga le colonne:")
            print("   Id, R, RM, Nome, Squadra")
            return

        # Step 4: Pulisci dati
        df_clean = self.clean_data(df)

        # Step 5: Preview
        self.show_preview(df_clean)

        # Step 6: Conferma salvataggio
        print("\n💾 Salvare come CSV?")
        confirm = input("   [S]ì / [N]o: ").strip().upper()

        if confirm != 'S':
            print("\n❌ Operazione annullata.")
            return

        # Step 7: Salva
        output_path = self.save_csv(df_clean)

        if output_path:
            print("\n" + "="*70)
            print("✅ CONVERSIONE COMPLETATA!")
            print("="*70)
            print()
            print(f"File salvato: {output_path}")
            print()
            print("📝 PROSSIMI PASSI:")
            print("   1. Aggiorna src/config.py con il nuovo nome file")
            print("   2. Esegui Premere_15_luglio_o_dopo.bat")
            print()
            print("="*70)

    def run_auto(self, file_path=None):
        """Esecuzione automatica (per integrazione con UI)"""
        # Cerca file se non fornito
        if not file_path:
            file_path = self.find_excel_file()
            if not file_path:
                return None, "Nessun file Excel trovato"

        # Leggi Excel
        df = self.read_excel(file_path)
        if df is None:
            return None, "Errore lettura file Excel"

        # Valida colonne
        if not self.validate_columns(df):
            return None, "Colonne richieste mancanti nel file"

        # Pulisci dati
        df_clean = self.clean_data(df)

        # Salva
        output_path = self.save_csv(df_clean)

        if output_path:
            return output_path, f"Convertiti {len(df_clean)} giocatori"
        else:
            return None, "Errore salvataggio CSV"


def main():
    """Entry point"""
    converter = QuotazioniConverter()
    converter.run_interactive()


if __name__ == "__main__":
    main()
