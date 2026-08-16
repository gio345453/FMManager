"""
Script Semi-Automatico per Aggiornamento Dati Stagione
Scarica classifica e clean sheets da FBref e genera codice Python pronto all'uso

Esecuzione: python scripts/update_season_data.py
Data consigliata: 10-20 Luglio di ogni anno
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import shutil
from pathlib import Path


class SeasonDataUpdater:
    """Gestisce download e conversione dati stagione da FBref"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FantaCalcio-Manager/1.0 (Educational/Personal Use)'
        })

        # URL FBref Serie A (aggiornare se cambia)
        self.base_url = "https://fbref.com"
        self.serie_a_url = "https://fbref.com/en/comps/11/Serie-A-Stats"

        # Mapping nomi squadre FBref → App
        self.team_name_mapping = {
            'Internazionale': 'Inter',
            'AC Milan': 'Milan',
            'Juventus': 'Juventus',
            'Atalanta': 'Atalanta',
            'Bologna': 'Bologna',
            'AS Roma': 'Roma',
            'Lazio': 'Lazio',
            'Fiorentina': 'Fiorentina',
            'Napoli': 'Napoli',
            'Torino': 'Torino',
            'Genoa': 'Genoa',
            'Monza': 'Monza',
            'Verona': 'Verona',
            'Lecce': 'Lecce',
            'Udinese': 'Udinese',
            'Cagliari': 'Cagliari',
            'Empoli': 'Empoli',
            'Parma': 'Parma',
            'Como': 'Como',
            'Venezia': 'Venezia',
            # Aggiungi altri mapping se necessario
        }

    def create_backup(self):
        """Crea backup dei file esistenti"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        files_to_backup = [
            'src/data/team_stats.py',
            'src/data/clean_sheets_data.py'
        ]

        print("\n📦 Creazione backup...")
        for file_path in files_to_backup:
            if Path(file_path).exists():
                backup_path = f"{file_path}.backup.{timestamp}"
                shutil.copy2(file_path, backup_path)
                print(f"   ✅ Backup: {backup_path}")
            else:
                print(f"   ⚠️  File non trovato: {file_path}")

    def normalize_team_name(self, fbref_name):
        """Normalizza nome squadra da FBref al formato app"""
        # Rimuovi spazi extra e standardizza
        name = fbref_name.strip()

        # Usa mapping se presente
        if name in self.team_name_mapping:
            return self.team_name_mapping[name]

        # Altrimenti prova a pulire
        # Rimuovi "FC", "AC", "AS", "US", etc.
        name = re.sub(r'\b(FC|AC|AS|US|SSC|ASD)\b', '', name).strip()

        return name

    def scrape_standings(self):
        """Scarica classifica Serie A da FBref"""
        print("\n🔍 Scaricamento classifica da FBref...")

        try:
            response = self.session.get(self.serie_a_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Trova tabella classifica (regular season)
            standings_table = soup.find('table', {'id': re.compile(r'results.*overall.*')})

            if not standings_table:
                print("   ❌ Tabella classifica non trovata")
                return None

            standings = []
            rows = standings_table.find('tbody').find_all('tr')

            for row in rows:
                # Salta righe di separazione
                if 'thead' in row.get('class', []):
                    continue

                cells = row.find_all(['th', 'td'])
                if len(cells) < 10:
                    continue

                try:
                    # Estrai dati
                    position = int(cells[0].text.strip())
                    team_name = cells[1].text.strip()
                    wins = int(cells[3].text.strip())
                    draws = int(cells[4].text.strip())
                    losses = int(cells[5].text.strip())
                    gf = int(cells[6].text.strip())
                    ga = int(cells[7].text.strip())
                    points = int(cells[9].text.strip())

                    # Normalizza nome squadra
                    normalized_name = self.normalize_team_name(team_name)

                    standings.append({
                        'posizione': position,
                        'nome': normalized_name,
                        'nome_originale': team_name,
                        'punti': points,
                        'vittorie': wins,
                        'pareggi': draws,
                        'sconfitte': losses,
                        'gol_fatti': gf,
                        'gol_subiti': ga
                    })
                except (ValueError, IndexError) as e:
                    print(f"   ⚠️  Errore parsing riga: {e}")
                    continue

            print(f"   ✅ Scaricate {len(standings)} squadre")
            return standings

        except requests.RequestException as e:
            print(f"   ❌ Errore connessione: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Errore imprevisto: {e}")
            return None

    def scrape_clean_sheets(self):
        """Scarica clean sheets portieri da FBref"""
        print("\n🧤 Scaricamento clean sheets da FBref...")

        try:
            response = self.session.get(self.serie_a_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Trova link a pagina goalkeeping
            gk_link = soup.find('a', string=re.compile(r'Goalkeeping', re.I))
            if not gk_link:
                print("   ❌ Link goalkeeping non trovato")
                return None

            gk_url = self.base_url + gk_link['href']
            print(f"   🔗 URL goalkeeping: {gk_url}")

            # Scarica pagina goalkeeping
            gk_response = self.session.get(gk_url, timeout=10)
            gk_response.raise_for_status()

            gk_soup = BeautifulSoup(gk_response.content, 'html.parser')

            # Trova tabella statistiche portieri
            gk_table = gk_soup.find('table', {'id': re.compile(r'stats_keeper.*')})

            if not gk_table:
                print("   ❌ Tabella portieri non trovata")
                return None

            clean_sheets = []
            rows = gk_table.find('tbody').find_all('tr')

            for row in rows:
                if 'thead' in row.get('class', []):
                    continue

                cells = row.find_all(['th', 'td'])
                if len(cells) < 15:
                    continue

                try:
                    # Nome portiere (prima colonna con link)
                    name_cell = cells[1]
                    player_name = name_cell.text.strip()

                    # Clean sheets (colonna CS - Clean Sheets)
                    # Tipicamente intorno alla colonna 14-16
                    cs_value = None
                    for i, cell in enumerate(cells):
                        if cell.get('data-stat') == 'gk_clean_sheets':
                            cs_value = int(cell.text.strip())
                            break

                    if cs_value is None:
                        # Fallback: prova posizione fissa (colonna ~14)
                        try:
                            cs_value = int(cells[14].text.strip())
                        except:
                            continue

                    # Aggiungi solo se ha giocato abbastanza (almeno 5 presenze)
                    matches_cell = None
                    for cell in cells:
                        if cell.get('data-stat') == 'games':
                            matches_cell = cell
                            break

                    if matches_cell:
                        matches = int(matches_cell.text.strip())
                        if matches < 5:
                            continue

                    # Normalizza nome (rimuovi accenti, standardizza)
                    normalized_name = self.normalize_goalkeeper_name(player_name)

                    clean_sheets.append({
                        'nome': normalized_name,
                        'nome_originale': player_name,
                        'clean_sheets': cs_value
                    })

                except (ValueError, IndexError) as e:
                    continue

            # Ordina per clean sheets (più alto primo)
            clean_sheets.sort(key=lambda x: x['clean_sheets'], reverse=True)

            print(f"   ✅ Scaricati {len(clean_sheets)} portieri")
            return clean_sheets

        except requests.RequestException as e:
            print(f"   ❌ Errore connessione: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Errore imprevisto: {e}")
            import traceback
            traceback.print_exc()
            return None

    def normalize_goalkeeper_name(self, name):
        """Normalizza nome portiere"""
        # Rimuovi suffissi
        name = re.sub(r'\s*\(.*?\)', '', name).strip()

        # Split nome cognome e prendi cognome
        parts = name.split()
        if len(parts) > 1:
            return parts[-1]  # Usa cognome
        return name

    def validate_standings(self, standings):
        """Valida dati classifica"""
        print("\n✅ Validazione classifica...")

        if not standings or len(standings) != 20:
            print(f"   ❌ Numero squadre errato: {len(standings)} (atteso: 20)")
            return False

        errors = []

        for team in standings:
            # Verifica partite giocate
            total_matches = team['vittorie'] + team['pareggi'] + team['sconfitte']
            if total_matches != 38:
                errors.append(f"   ⚠️  {team['nome']}: partite = {total_matches} (atteso: 38)")

            # Verifica punti
            expected_points = (team['vittorie'] * 3) + team['pareggi']
            if team['punti'] != expected_points:
                errors.append(f"   ⚠️  {team['nome']}: punti = {team['punti']} (atteso: {expected_points})")

        if errors:
            print("\n   ⚠️  WARNINGS trovati:")
            for error in errors:
                print(error)
            return False

        print("   ✅ Validazione OK!")
        return True

    def validate_clean_sheets(self, clean_sheets):
        """Valida dati clean sheets"""
        print("\n✅ Validazione clean sheets...")

        if not clean_sheets or len(clean_sheets) < 15:
            print(f"   ⚠️  Pochi portieri trovati: {len(clean_sheets)} (min: 15)")
            return False

        print(f"   ✅ {len(clean_sheets)} portieri validati")
        return True

    def generate_team_stats_code(self, standings):
        """Genera codice Python per team_stats.py"""
        code = "CLASSIFICA_REALE_CURRENT_SEASON = {\n"

        for team in standings:
            code += f"    '{team['nome']}': {{\n"
            code += f"        'posizione': {team['posizione']},\n"
            code += f"        'punti': {team['punti']},\n"
            code += f"        'vittorie': {team['vittorie']},\n"
            code += f"        'pareggi': {team['pareggi']},\n"
            code += f"        'sconfitte': {team['sconfitte']},\n"
            code += f"        'gol_fatti': {team['gol_fatti']},\n"
            code += f"        'gol_subiti': {team['gol_subiti']}\n"
            code += "    },\n"

        code += "}\n"
        return code

    def generate_clean_sheets_code(self, clean_sheets):
        """Genera codice Python per clean_sheets_data.py"""
        code = "CLEAN_SHEETS_CURRENT_SEASON = {\n"

        for gk in clean_sheets:
            # Aggiungi commento con nome originale se diverso
            if gk['nome'] != gk['nome_originale']:
                code += f"    '{gk['nome']}': {gk['clean_sheets']},  # {gk['nome_originale']}\n"
            else:
                code += f"    '{gk['nome']}': {gk['clean_sheets']},\n"

        code += "}\n"
        return code

    def show_preview(self, standings, clean_sheets):
        """Mostra preview dati scaricati"""
        print("\n" + "="*60)
        print("📋 PREVIEW DATI SCARICATI")
        print("="*60)

        if standings:
            print("\n🏆 CLASSIFICA SERIE A (Top 10):")
            print("-" * 60)
            for i, team in enumerate(standings[:10], 1):
                print(f"{i:2}. {team['nome']:20} - {team['punti']:2} pts "
                      f"(W:{team['vittorie']:2} D:{team['pareggi']:2} L:{team['sconfitte']:2})")
            print(f"   ... e altre {len(standings) - 10} squadre")

        if clean_sheets:
            print("\n🧤 CLEAN SHEETS PORTIERI (Top 15):")
            print("-" * 60)
            for i, gk in enumerate(clean_sheets[:15], 1):
                print(f"{i:2}. {gk['nome']:20} - {gk['clean_sheets']:2} CS")
            if len(clean_sheets) > 15:
                print(f"   ... e altri {len(clean_sheets) - 15} portieri")

        print("\n" + "="*60)

    def save_to_file(self, standings_code, clean_sheets_code):
        """Salva codice generato in file temporanei"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')

        output_dir = Path('scripts/output')
        output_dir.mkdir(exist_ok=True)

        # Salva team_stats
        team_stats_file = output_dir / f'team_stats_generated_{timestamp}.py'
        with open(team_stats_file, 'w', encoding='utf-8') as f:
            f.write("# Codice generato automaticamente\n")
            f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(standings_code)

        print(f"\n💾 Salvato: {team_stats_file}")

        # Salva clean_sheets
        clean_sheets_file = output_dir / f'clean_sheets_generated_{timestamp}.py'
        with open(clean_sheets_file, 'w', encoding='utf-8') as f:
            f.write("# Codice generato automaticamente\n")
            f.write(f"# Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(clean_sheets_code)

        print(f"💾 Salvato: {clean_sheets_file}")

        return team_stats_file, clean_sheets_file

    def run(self):
        """Esegue il processo completo"""
        print("\n" + "="*60)
        print("⚽ AGGIORNAMENTO DATI STAGIONE - SERIE A")
        print("="*60)

        # Step 1: Backup
        self.create_backup()

        # Step 2: Scarica dati
        standings = self.scrape_standings()
        clean_sheets = self.scrape_clean_sheets()

        if not standings and not clean_sheets:
            print("\n❌ Nessun dato scaricato. Uscita.")
            return

        # Step 3: Valida
        standings_valid = self.validate_standings(standings) if standings else False
        clean_sheets_valid = self.validate_clean_sheets(clean_sheets) if clean_sheets else False

        # Step 4: Preview
        self.show_preview(standings, clean_sheets)

        # Step 5: Genera codice
        if standings:
            standings_code = self.generate_team_stats_code(standings)
        else:
            standings_code = None

        if clean_sheets:
            clean_sheets_code = self.generate_clean_sheets_code(clean_sheets)
        else:
            clean_sheets_code = None

        # Step 6: Salva
        print("\n" + "="*60)
        print("💾 SALVATAGGIO")
        print("="*60)

        if standings_code or clean_sheets_code:
            files = self.save_to_file(
                standings_code or "# Nessun dato",
                clean_sheets_code or "# Nessun dato"
            )

            print("\n✅ COMPLETATO!")
            print("\n📝 PROSSIMI PASSI:")
            print("1. Controlla i file generati in scripts/output/")
            print("2. Copia il contenuto nei file originali:")
            print("   - scripts/output/team_stats_generated_*.py → src/data/team_stats.py")
            print("   - scripts/output/clean_sheets_generated_*.py → src/data/clean_sheets_data.py")
            print("3. Verifica manualmente i nomi squadre e portieri")
            print("4. Testa l'applicazione")
        else:
            print("\n❌ Nessun codice generato")


def main():
    """Entry point"""
    updater = SeasonDataUpdater()
    updater.run()


if __name__ == "__main__":
    main()
