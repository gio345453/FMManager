"""
Scarica e aggiorna il calendario della Serie A tramite football-data.org API v4.

Richiede un file API_KEY.txt nella stessa cartella di questo script:
    App/data/Calendario/API_KEY.txt

La chiave viene inviata nell'header:
    X-Auth-Token: <API_KEY>
"""

import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import requests


class CalendarioSerieADownloader:
    """Scarica il calendario Serie A da football-data.org."""

    BASE_URL = "https://api.football-data.org/v4"
    COMPETITION_CODE = "SA"

    def __init__(self, season: str = "2026-27"):
        self.season = season
        self.season_start_year = self._extract_season_start_year(season)
        self.output_dir = Path(__file__).resolve().parent
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key_path = self.output_dir / "API_KEY.txt"
        self.session = requests.Session()

        # Nomi standard usati dal resto dell'app.
        self.team_mapping = {
            "ATALANTA": "Atalanta",
            "BOLOGNA": "Bologna",
            "CAGLIARI": "Cagliari",
            "COMO": "Como",
            "CREMONESE": "Cremonese",
            "EMPOLI": "Empoli",
            "FIORENTINA": "Fiorentina",
            "GENOA": "Genoa",
            "INTER": "Inter",
            "JUVENTUS": "Juventus",
            "LAZIO": "Lazio",
            "LECCE": "Lecce",
            "MILAN": "Milan",
            "MONZA": "Monza",
            "NAPOLI": "Napoli",
            "PARMA": "Parma",
            "PISA": "Pisa",
            "ROMA": "Roma",
            "SASSUOLO": "Sassuolo",
            "TORINO": "Torino",
            "UDINESE": "Udinese",
            "VENEZIA": "Venezia",
            "VERONA": "Verona",
        }

    @staticmethod
    def _extract_season_start_year(season: str) -> int:
        """Converte 2026-27 / 2026/27 / 2026 in 2026."""
        match = re.search(r"\d{4}", str(season))
        if not match:
            raise ValueError(f"Formato stagione non valido: {season}")
        return int(match.group())

    def _read_api_key(self) -> Optional[str]:
        """Legge la chiave dal file API_KEY.txt senza stamparla nei log."""
        if not self.api_key_path.exists():
            print(f"[Calendar] ERRORE: file API key non trovato: {self.api_key_path}")
            return None

        try:
            key = self.api_key_path.read_text(encoding="utf-8-sig").strip()
            # Tolleriamo una riga del tipo API_KEY=xxxxx.
            if key.upper().startswith("API_KEY="):
                key = key.split("=", 1)[1].strip()
            if not key:
                print("[Calendar] ERRORE: API_KEY.txt è vuoto")
                return None
            return key
        except Exception as exc:
            print(f"[Calendar] ERRORE lettura API_KEY.txt: {exc}")
            return None

    def _headers(self) -> Optional[dict]:
        key = self._read_api_key()
        if not key:
            return None
        return {
            "X-Auth-Token": key,
            "Accept": "application/json",
            "User-Agent": "FantaCalcioManager/1.0",
        }

    def download_from_football_data(self):
        """Scarica tutte le partite della stagione Serie A indicata."""
        headers = self._headers()
        if not headers:
            return None

        url = f"{self.BASE_URL}/competitions/{self.COMPETITION_CODE}/matches"
        params = {
            "season": self.season_start_year,
            "limit": 500,
        }

        print(f"[Calendar] Football-data URL: {url}?season={self.season_start_year}&limit=500")

        try:
            response = self.session.get(url, headers=headers, params=params, timeout=20)
            print(f"[Calendar] Football-data HTTP {response.status_code}")

            if response.status_code == 401:
                print("[Calendar] ERRORE 401: API key non valida o non autorizzata")
                return None
            if response.status_code == 403:
                print("[Calendar] ERRORE 403: piano/API key non abilita questa risorsa")
                return None
            if response.status_code == 429:
                retry_after = response.headers.get("X-Requests-Available-Minute")
                print(f"[Calendar] ERRORE 429: limite richieste raggiunto (disponibili minuto: {retry_after})")
                return None
            if response.status_code != 200:
                print(f"[Calendar] Football-data errore HTTP: {response.status_code}")
                return None

            payload = response.json()
            matches_payload = payload.get("matches", []) if isinstance(payload, dict) else []
            if not isinstance(matches_payload, list):
                print("[Calendar] Risposta API inattesa: 'matches' non è una lista")
                return None

            matches = self._parse_football_data_response(matches_payload)
            if not matches:
                print("[Calendar] API ha restituito 0 partite valide")
                return None

            return matches

        except requests.RequestException as exc:
            print(f"[Calendar] Errore connessione football-data: {exc}")
            return None
        except ValueError as exc:
            print(f"[Calendar] JSON football-data non valido: {exc}")
            return None
        except Exception as exc:
            print(f"[Calendar] Errore download football-data: {exc}")
            return None

    def _parse_football_data_response(self, matches_payload):
        """Converte la risposta football-data nel formato atteso dall'app."""
        matches = []

        for item in matches_payload:
            try:
                matchday = item.get("matchday")
                home = item.get("homeTeam") or {}
                away = item.get("awayTeam") or {}
                score = item.get("score") or {}
                full_time = score.get("fullTime") or {}

                home_raw = home.get("name") or home.get("shortName")
                away_raw = away.get("name") or away.get("shortName")

                if not home_raw or not away_raw or not matchday:
                    continue

                home_team = self._normalize_team_name(home_raw)
                away_team = self._normalize_team_name(away_raw)

                if not home_team or not away_team:
                    continue

                home_goals = self._to_int(full_time.get("home"))
                away_goals = self._to_int(full_time.get("away"))
                status = str(item.get("status") or "").upper()

                # FINISHED è la fonte principale per capire se il match è concluso.
                # I gol costituiscono un'ulteriore conferma; 0-0 è quindi valido.
                played = status == "FINISHED" and home_goals is not None and away_goals is not None

                utc_date = item.get("utcDate")
                match_date = self._normalize_date(utc_date)

                matches.append({
                    "matchday": int(matchday),
                    "date": match_date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "played": played,
                })

            except Exception as exc:
                print(f"[Calendar] Errore parsing match football-data: {exc}")

        # Evita eventuali duplicati.
        unique = {}
        for match in matches:
            key = (
                match["matchday"],
                match["home_team"],
                match["away_team"],
            )
            unique[key] = match

        return list(unique.values())

    @staticmethod
    def _to_int(value):
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_date(value):
        if not value:
            return None
        text = str(value)
        # utcDate tipicamente: 2026-08-28T18:45:00Z
        return text[:10]

    def _normalize_team_name(self, team_name):
        if not team_name:
            return None

        team_upper = str(team_name).upper().strip()
        aliases = {
            "FC INTERNAZIONALE MILANO": "INTER",
            "INTER MILANO": "INTER",
            "AC MILAN": "MILAN",
            "ACF FIORENTINA": "FIORENTINA",
            "AS ROMA": "ROMA",
            "SS LAZIO": "LAZIO",
            "SSC NAPOLI": "NAPOLI",
            "HELLAS VERONA FC": "VERONA",
            "UDINESE CALCIO": "UDINESE",
            "TORINO FC": "TORINO",
            "BOLOGNA FC 1909": "BOLOGNA",
            "PARMA CALCIO 1913": "PARMA",
            "US LECCE": "LECCE",
            "COMO 1907": "COMO",
            "GENOA CFC": "GENOA",
        }
        team_upper = aliases.get(team_upper, team_upper)

        # Rimuovi alcuni prefissi comuni.
        team_upper = re.sub(r"^(FC|AC|US|SSC|UC|AS|SS)\s+", "", team_upper)

        return self.team_mapping.get(team_upper, str(team_name).title())

    def download(self):
        """Punto di ingresso unico: football-data.org."""
        print(f"[Calendar] Scaricamento Serie A {self.season} da football-data.org...")
        matches = self.download_from_football_data()

        if matches:
            print(f"[Calendar] Football-data: ricevute {len(matches)} partite")
            return matches

        print("[Calendar] Football-data non ha restituito il calendario")
        return None

    def save(self, matches):
        """Salva calendario stagionale e file canonico usato dall'app."""
        if not matches:
            return None

        data = {
            "season": self.season,
            "download_date": datetime.now().isoformat(),
            "source": "football-data.org",
            "total_matches": len(matches),
            "matches": matches,
        }

        seasonal_file = self.output_dir / f"calendario_seriea_{self.season.replace('-', '_')}.json"
        canonical_file = self.output_dir / "calendario.json"

        for target in (seasonal_file, canonical_file):
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[Calendar] Salvato calendario canonico: {canonical_file}")
        return canonical_file

    def validate(self, matches):
        """Valida il calendario completo prima di sovrascrivere il file locale."""
        if not matches:
            return False

        matchdays = {m.get("matchday") for m in matches if m.get("matchday")}
        teams = set()
        for match in matches:
            if match.get("home_team"):
                teams.add(match["home_team"])
            if match.get("away_team"):
                teams.add(match["away_team"])

        valid = True

        if len(matches) != 380:
            print(f"[Calendar] NON valido: {len(matches)} partite invece di 380")
            valid = False

        if len(matchdays) != 38:
            print(f"[Calendar] NON valido: {len(matchdays)} giornate invece di 38")
            valid = False

        if len(teams) != 20:
            print(f"[Calendar] NON valido: {len(teams)} squadre invece di 20")
            print(f"[Calendar] Squadre trovate: {sorted(teams)}")
            valid = False

        if valid:
            print("[Calendar] Validato: 380 partite, 38 giornate, 20 squadre")

        return valid


def _calendar_needs_refresh(path: Path) -> bool:
    """Forza refresh se esistono gare già passate senza risultato."""
    if not path.exists():
        return True

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("matches", [])
        if not matches:
            return True

        today = date.today()

        for match in matches:
            date_raw = match.get("date")
            if not date_raw or match.get("played"):
                continue

            try:
                parsed = datetime.fromisoformat(str(date_raw)[:10]).date()
            except Exception:
                parsed = None

            if parsed and parsed <= today:
                return True

        return len(matches) != 380

    except Exception:
        return True


def sync_current_calendar(season="2026-27", max_age_hours=6):
    """
    Controlla e aggiorna automaticamente il calendario.

    Il controllo non si basa solo sull'età del file: una partita già passata
    senza risultato forza comunque un nuovo download dall'API.
    """
    canonical_file = Path(__file__).resolve().parent / "calendario.json"

    try:
        if canonical_file.exists():
            age_hours = (
                datetime.now().timestamp() - canonical_file.stat().st_mtime
            ) / 3600.0

            if age_hours < max_age_hours and not _calendar_needs_refresh(canonical_file):
                print(f"[Calendar] Calendario locale valido e recente ({age_hours:.1f}h)")
                return canonical_file

            if _calendar_needs_refresh(canonical_file):
                print("[Calendar] Calendario da aggiornare: contiene partite passate senza risultato")
        else:
            print("[Calendar] calendario.json assente: download necessario")

        downloader = CalendarioSerieADownloader(season=season)
        print("[Calendar] Fonte: football-data.org API")
        matches = downloader.download()

        if not matches:
            print("[Calendar] Impossibile aggiornare il calendario da football-data.org")
            return canonical_file if canonical_file.exists() else None

        print(f"[Calendar] Ricevute {len(matches)} partite")
        if not downloader.validate(matches):
            print("[Calendar] Download non valido: NON sovrascrivo il file locale")
            return canonical_file if canonical_file.exists() else None

        saved = downloader.save(matches)

        # Dopo un aggiornamento riuscito, invalida il singleton che usa il calendario.
        try:
            from src.data.fixture_difficulty import invalidate_fixture_calculator
            invalidate_fixture_calculator()
            print("[Calendar] FixtureDifficultyCalculator invalidato: nuovo calendario rilevato")
        except Exception as exc:
            print(f"[Calendar] Avviso: impossibile invalidare FixtureDifficultyCalculator: {exc}")

        return saved

    except Exception as exc:
        print(f"[Calendar] Errore aggiornamento: {type(exc).__name__}: {exc}")
        return canonical_file if canonical_file.exists() else None


def main():
    """Esegue il download manuale del calendario."""
    import argparse

    parser = argparse.ArgumentParser(description="Scarica calendario Serie A da football-data.org")
    parser.add_argument("--season", default="2026-27", help="Stagione (es. 2026-27)")
    args = parser.parse_args()

    downloader = CalendarioSerieADownloader(season=args.season)
    matches = downloader.download()

    if not matches:
        print("[Calendar] Download fallito")
        return 1

    if not downloader.validate(matches):
        print("[Calendar] Download non valido: file NON salvato")
        return 1

    output_file = downloader.save(matches)

    if output_file:
        print("[Calendar] Calendario salvato con successo")
        print(f"[Calendar] File: {output_file}")
        return 0

    print("[Calendar] Errore nel salvataggio")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
