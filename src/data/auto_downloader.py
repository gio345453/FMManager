"""
Gestisce il download automatico dei dati di tiratori e titolarità con controllo temporale
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class AutoDownloader:
    """Gestisce il download automatico dei dati con limitazione temporale"""

    def __init__(self):
        # Path assoluto dalla root del progetto
        _ROOT_DIR = Path(__file__).parent.parent.parent
        self.cache_file = _ROOT_DIR / 'data' / 'last_download.json'
        self.min_interval_hours = {
            'titolarita': 1,
            'tiratori': 24,
        }

    def _load_cache(self):
        """Carica la cache con l'ultimo timestamp di download"""
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento della cache: {e}")
            return {}

    def _save_cache(self, cache_data):
        """Salva la cache con i timestamp di download"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Errore nel salvataggio della cache: {e}")

    def should_download(self, data_type):
        """
        Verifica se è necessario scaricare i dati

        Args:
            data_type: Tipo di dati ('tiratori' o 'titolarita')

        Returns:
            bool: True se bisogna scaricare, False altrimenti
        """
        cache = self._load_cache()
        last_download_str = cache.get(data_type)

        if not last_download_str:
            return True

        try:
            last_download = datetime.fromisoformat(last_download_str)
            now = datetime.now()
            time_diff = now - last_download

            min_interval = self.min_interval_hours.get(data_type, 1)
            return time_diff >= timedelta(hours=min_interval)
        except Exception as e:
            print(f"Errore nel parsing della data: {e}")
            return True

    def mark_downloaded(self, data_type):
        """
        Segna i dati come scaricati aggiornando il timestamp

        Args:
            data_type: Tipo di dati ('tiratori' o 'titolarita')
        """
        cache = self._load_cache()
        cache[data_type] = datetime.now().isoformat()
        self._save_cache(cache)

    def download_tiratori(self):
        """Scarica i dati dei tiratori se necessario"""
        if not self.should_download('tiratori'):
            print("Skip download tiratori (scaricato meno di 24 ore fa)")
            return False

        print("Download tiratori in corso...")
        try:
            # Importa e esegue lo scraping
            import sys
            _ROOT_DIR = Path(__file__).parent.parent.parent
            tiratori_path = _ROOT_DIR / 'data' / 'Tiratori'
            sys.path.insert(0, str(tiratori_path))

            from Tiratori import scrape_tiratori
            scrape_tiratori()

            # Segna come scaricato
            self.mark_downloaded('tiratori')
            print("Download tiratori completato")
            return True

        except Exception as e:
            print(f"Errore nel download tiratori: {e}")
            return False
        finally:
            if str(tiratori_path) in sys.path:
                sys.path.remove(str(tiratori_path))

    def download_titolarita(self):
        """Scarica i dati della titolarità se necessario"""
        if not self.should_download('titolarita'):
            print("⏭️ Skip download titolarità (scaricato meno di 1 ora fa)")
            return False

        print("📥 Download titolarità in corso...")
        try:
            # Importa e esegue lo scraping
            import sys
            titolarita_path = Path('data') / 'Titolarita'
            sys.path.insert(0, str(titolarita_path))

            from Titolarita import scrape_probabili_formazioni
            scrape_probabili_formazioni()

            # Segna come scaricato
            self.mark_downloaded('titolarita')
            print("✅ Download titolarità completato")
            return True

        except Exception as e:
            print(f"❌ Errore nel download titolarità: {e}")
            return False
        finally:
            if str(titolarita_path) in sys.path:
                sys.path.remove(str(titolarita_path))

    def download_all(self):
        """
        Scarica tutti i dati necessari

        Returns:
            dict: Dizionario con i risultati dei download
        """
        results = {
            'tiratori': self.download_tiratori(),
            'titolarita': self.download_titolarita()
        }
        return results
