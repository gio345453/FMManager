"""
Script per scaricare gol fatti/subiti delle squadre Serie A da FBref
Scarica dati dinamicamente in base alla stagione corrente
Genera file JSON con i dati per calcolare team_strength

Uso:
    python data/Calendario/download_team_stats.py
    python data/Calendario/download_team_stats.py --seasons 2025-26 2024-25 2023-24
    python data/Calendario/download_team_stats.py --history-count 3
    python data/Calendario/download_team_stats.py --output custom_output.json
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Aggiungi root al path per importare src.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.config import get_historical_seasons, parse_season


class FBrefTeamStatsDownloader:
    """Scarica statistiche squadre Serie A da FBref con merge sicuro"""

    def __init__(self, output_file: str = 'Aggiornamento_Fine_Stagione/team_stats_fbref.json'):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        self.output_file = Path(output_file)

        # Mappa nomi squadre FBref → nomi standard
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
            # Varianti nome
            'Hellas Verona': 'Verona',
            'AC Milan': 'Milan',
            'Inter Milan': 'Inter',
            'Internazionale': 'Inter',
            'AS Roma': 'Roma',
            # Retrocesse/promosse altre stagioni
            'Sassuolo': 'Sassuolo',
            'Salernitana': 'Salernitana',
            'Spezia': 'Spezia',
            'Cremonese': 'Cremonese',
            'Sampdoria': 'Sampdoria',
            'Frosinone': 'Frosinone'
        }

    @staticmethod
    def build_fbref_url(season: str) -> str:
        """
        Costruisce l'URL FBref per una stagione.

        Args:
            season: stagione formato 'YYYY-YY' (es. '2025-26')

        Returns:
            str: URL FBref completo

        Examples:
            >>> build_fbref_url('2025-26')
            'https://fbref.com/en/comps/11/Serie-A-Stats'
            >>> build_fbref_url('2024-25')
            'https://fbref.com/en/comps/11/2024-2025/2024-2025-Serie-A-Stats'
        """
        year_start = parse_season(season)
        if year_start is None:
            raise ValueError(f"Stagione non valida: {season}")

        current_year = datetime.now().year
        # La stagione corrente/più recente usa URL senza anno
        if year_start >= current_year - 1:
            return 'https://fbref.com/en/comps/11/Serie-A-Stats'

        # Stagioni passate usano formato esteso
        year_end = year_start + 1
        season_long = f"{year_start}-{year_end}"
        return f'https://fbref.com/en/comps/11/{season_long}/{season_long}-Serie-A-Stats'

    def load_existing_data(self) -> dict:
        """Carica dati esistenti dal file JSON per merge sicuro."""
        if not self.output_file.exists():
            return {}

        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Impossibile caricare dati esistenti: {e}")
            return {}

    def normalize_team_name(self, name):
        """Normalizza nome squadra"""
        name = name.strip()
        return self.team_mapping.get(name, name)

    def download_season_stats(self, season, url):
        """
        Scarica statistiche squadre per una stagione con validazione.

        Returns:
            dict: {squadra: {'position': X, 'gf': X, 'gs': Y, 'punti': Z, 'partite': N}} o None se fallito
        """
        print(f"\n{'='*60}")
        print(f"Scaricamento stagione {season}")
        print(f"URL: {url}")
        print('='*60)

        try:
            response = self.session.get(url, timeout=15)

            if response.status_code == 403:
                print(f"⚠️ 403 Forbidden - FBref blocca lo scraping")
                print(f"   Alternativa: usa dati manuali da fonti ufficiali")
                return None

            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Trova la tabella della classifica
            table = soup.find('table', {'class': 'stats_table'})

            if not table:
                print(f"⚠️ Tabella non trovata per {season}")
                return None

            stats = {}
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                try:
                    # Skip righe di intestazione
                    if row.find('th', {'class': 'thead'}):
                        continue

                    cells = row.find_all(['th', 'td'])

                    if len(cells) < 10:
                        continue

                    # Estrai dati: Pos, Squad, MP, W, D, L, GF, GA, GD, Pts
                    team_cell = cells[0]
                    team_name = team_cell.get_text(strip=True)
                    team_name = self.normalize_team_name(team_name)

                    position = int(cells[0].get_text(strip=True))
                    partite = int(cells[2].get_text(strip=True))
                    gf = int(cells[6].get_text(strip=True))
                    gs = int(cells[7].get_text(strip=True))
                    punti = int(cells[9].get_text(strip=True))

                    stats[team_name] = {
                        'position': position,
                        'gf': gf,
                        'gs': gs,
                        'punti': punti,
                        'partite': partite
                    }

                    print(f"✓ {team_name:15} → GF:{gf:3} GS:{gs:3} Pt:{punti:3} ({partite} partite)")

                except (ValueError, IndexError) as e:
                    print(f"⚠️ Errore parsing {team_name if 'team_name' in locals() else 'riga'}: {e}")
                    continue

            # Validazione: Serie A deve avere 20 squadre
            if len(stats) < 18:
                print(f"⚠️ Stagione {season} ha solo {len(stats)} squadre (minimo 18 per Serie A)")
                return None

            print(f"\n✅ Scaricate {len(stats)} squadre per {season}")
            return stats

        except Exception as e:
            print(f"❌ Errore download {season}: {e}")
            return None

    def validate_season_data(self, season: str, stats: dict) -> bool:
        """
        Valida i dati di una stagione.

        Returns:
            bool: True se i dati sono validi per Serie A
        """
        if not stats or len(stats) < 18:
            return False

        # Verifica che tutti i team abbiano dati numerici validi
        for team, data in stats.items():
            try:
                if data['gf'] < 0 or data['gs'] < 0 or data['partite'] <= 0:
                    return False
            except (KeyError, TypeError):
                return False

        return True

    def download_all_seasons(self, seasons: list[str]) -> dict[str, dict]:
        """
        Scarica dati per le stagioni specificate e fa merge con dati esistenti.

        Args:
            seasons: lista di stagioni da scaricare (es. ['2025-26', '2024-25'])

        Returns:
            dict: dati combinati con metadata
        """
        existing_data = self.load_existing_data()

        # Estrai dati esistenti e metadata
        existing_seasons = {k: v for k, v in existing_data.items() if k != '_meta'}
        existing_meta = existing_data.get('_meta', {'seasons': {}})

        updated_seasons = existing_seasons.copy()
        updated_meta = {'seasons': existing_meta.get('seasons', {}).copy()}

        for season in seasons:
            try:
                url = self.build_fbref_url(season)
            except ValueError as e:
                print(f"⚠️ {e}")
                continue

            stats = self.download_season_stats(season, url)

            if stats and self.validate_season_data(season, stats):
                updated_seasons[season] = stats
                updated_meta['seasons'][season] = {
                    'league': 'Serie A',
                    'source': 'fbref',
                    'downloaded_at': datetime.now().isoformat(),
                    'team_count': len(stats),
                    'url': url
                }
                print(f"✅ Stagione {season} aggiornata con successo")
            else:
                print(f"⚠️ Stagione {season} non valida, mantengo dati esistenti")
                # Preserva dati esistenti se il download fallisce
                if season in existing_seasons:
                    print(f"   → Dati precedenti di {season} conservati")

            # Pausa tra richieste
            time.sleep(2)

        return {'_meta': updated_meta, **updated_seasons}

    def save_to_json(self, data: dict) -> None:
        """Salva i dati in formato JSON con metadata."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Dati salvati in: {self.output_file}")

    def generate_summary(self, data):
        """Genera un riepilogo leggibile"""
        print("\n" + "="*80)
        print("RIEPILOGO DATI SCARICATI")
        print("="*80)

        seasons_data = {k: v for k, v in data.items() if k != '_meta'}

        for season, teams in seasons_data.items():
            print(f"\n📊 Stagione {season}: {len(teams)} squadre")

            if not teams:
                print("   (Nessun dato)")
                continue

            # Top 5 per gol fatti
            top_gf = sorted(teams.items(), key=lambda x: x[1].get('gf', 0), reverse=True)[:5]
            print("\n   Top 5 Gol Fatti:")
            for i, (team, stats) in enumerate(top_gf, 1):
                print(f"   {i}. {team:15} {stats['gf']:3} gol")

            # Top 5 per difesa (meno gol subiti)
            top_gs = sorted(teams.items(), key=lambda x: x[1].get('gs', 999))[:5]
            print("\n   Top 5 Difesa (meno gol subiti):")
            for i, (team, stats) in enumerate(top_gs, 1):
                print(f"   {i}. {team:15} {stats['gs']:3} gol subiti")


def main():
    parser = argparse.ArgumentParser(
        description='Scarica statistiche squadre Serie A da FBref',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python data/Calendario/download_team_stats.py
  python data/Calendario/download_team_stats.py --seasons 2025-26 2024-25
  python data/Calendario/download_team_stats.py --history-count 3
  python data/Calendario/download_team_stats.py --output custom.json
        """
    )

    parser.add_argument(
        '--seasons',
        nargs='+',
        help='Stagioni specifiche da scaricare (es. 2025-26 2024-25)'
    )
    parser.add_argument(
        '--history-count',
        type=int,
        default=3,
        help='Numero di stagioni storiche da scaricare (default: 3)'
    )
    parser.add_argument(
        '--output',
        default='Aggiornamento_Fine_Stagione/team_stats_fbref.json',
        help='File output (default: Aggiornamento_Fine_Stagione/team_stats_fbref.json)'
    )

    args = parser.parse_args()

    print("="*80)
    print("DOWNLOAD STATISTICHE SQUADRE SERIE A DA FBREF")
    print("="*80)

    # Determina quali stagioni scaricare
    if args.seasons:
        seasons = args.seasons
        print(f"\nStagioni specificate: {', '.join(seasons)}")
    else:
        seasons = get_historical_seasons(args.history_count)
        print(f"\nStagioni automatiche (ultime {args.history_count} concluse): {', '.join(seasons)}")

    print("="*80)

    downloader = FBrefTeamStatsDownloader(output_file=args.output)

    # Scarica dati con merge sicuro
    all_data = downloader.download_all_seasons(seasons)

    # Salva su file
    downloader.save_to_json(all_data)

    # Mostra riepilogo
    downloader.generate_summary(all_data)

    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETATO!")
    print("="*80)
    print("\nProssimo step: Usa questi dati per generare team_strength.json")
    print("Comando: python Aggiornamento_Fine_Stagione/calculate_team_strength.py")


if __name__ == "__main__":
    main()
