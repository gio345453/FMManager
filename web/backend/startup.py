"""
Startup unico del backend FMManager.

Questo è il file eseguito da launchers/avvia_app.bat:
    python web\\backend\\startup.py
"""
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# /App/web/backend/startup.py -> /App
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def run_startup_tasks():
    """Esegue tutti i task prima di avviare Uvicorn."""
    print("\n" + "=" * 64, flush=True)
    print("FMManager BACKEND - STARTUP", flush=True)
    print(f"Project root: {ROOT_DIR}", flush=True)
    print("=" * 64, flush=True)

    # 1. Calendario
    print("\n[1/4] Controllo/Aggiornamento calendario...", flush=True)
    try:
        from data.Calendario.download_calendario import sync_current_calendar
        from src.data.fixture_difficulty import invalidate_fixture_calculator

        calendar_path = sync_current_calendar(season="2026-27", max_age_hours=6)
        invalidate_fixture_calculator()

        if calendar_path:
            print(f"[Calendar] Pronto: {calendar_path}", flush=True)
        else:
            print("[Calendar] Nessun file disponibile.", flush=True)
    except Exception as exc:
        print(f"[Calendar] ERRORE: {type(exc).__name__}: {exc}", flush=True)

    # 2. Titolarità + tiratori
    print("\n[2/4] Aggiornamento titolarità e tiratori...", flush=True)
    try:
        from src.data.auto_downloader import AutoDownloader

        downloader = AutoDownloader()
        result_tit = downloader.download_titolarita()
        result_tir = downloader.download_tiratori()

        print(
            f"[AutoDownload] titolarita={result_tit} | tiratori={result_tir}",
            flush=True,
        )
    except Exception as exc:
        print(f"[AutoDownload] ERRORE: {type(exc).__name__}: {exc}", flush=True)

    # 3. Caricamento giocatori
    print("\n[3/4] Caricamento database giocatori...", flush=True)
    try:
        from src.data.calculator import StatsCalculator

        calc = StatsCalculator()
        df = calc.calculate_weighted_stats()
        if df is None:
            print("[Players] ERRORE: StatsCalculator ha restituito None", flush=True)
            return False

        print(f"[Players] Caricati {len(df)} giocatori", flush=True)
    except Exception as exc:
        print(f"[Players] ERRORE: {type(exc).__name__}: {exc}", flush=True)
        return False

    # 4. Tag
    print("\n[4/4] Assegnazione tag automatici...", flush=True)
    try:
        from src.data.auto_tags import AutoTagsManager

        AutoTagsManager().assign_auto_tags(df)
        print("[AutoTags] Completato", flush=True)
    except Exception as exc:
        print(f"[AutoTags] ERRORE: {type(exc).__name__}: {exc}", flush=True)

    print("\n" + "=" * 64, flush=True)
    print("STARTUP COMPLETATO - Avvio server...", flush=True)
    print("=" * 64 + "\n", flush=True)
    return True


if __name__ == "__main__":
    if not run_startup_tasks():
        raise SystemExit(1)

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(ROOT_DIR / "web" / "backend")],
    )
