"""
Script automatico per aggiornare team_strength.json
Eseguito automaticamente dopo aggiornamento listone
Può essere eseguito manualmente in qualsiasi momento

Esecuzione:
    python scripts/update_team_strength.py
    python scripts/update_team_strength.py --refresh-team-stats
    python scripts/update_team_strength.py --refresh-team-stats --history-count 3
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_script(script_path, description, extra_args=None):
    """Esegue uno script Python e gestisce errori"""
    print(f"\n{'='*70}")
    print(f"⚙️  {description}")
    print('='*70)

    cmd = ['python', script_path]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=False,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {description} completato")
            return True
        else:
            print(f"⚠️  {description} terminato con errori")
            return False

    except Exception as e:
        print(f"❌ Errore esecuzione {script_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Aggiorna team_strength.json con pipeline completa',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python scripts/update_team_strength.py
  python scripts/update_team_strength.py --refresh-team-stats
  python scripts/update_team_strength.py --refresh-team-stats --history-count 3
        """
    )

    parser.add_argument(
        '--refresh-team-stats',
        action='store_true',
        help='Scarica nuovi dati FBref prima di calcolare (default: usa dati esistenti)'
    )
    parser.add_argument(
        '--history-count',
        type=int,
        default=3,
        help='Numero di stagioni storiche da scaricare (default: 3, solo con --refresh-team-stats)'
    )
    parser.add_argument(
        '--seasons',
        nargs='+',
        help='Stagioni specifiche da scaricare (es. 2025-26 2024-25, solo con --refresh-team-stats)'
    )

    args = parser.parse_args()

    print("="*70)
    print("🔄 AGGIORNAMENTO AUTOMATICO TEAM STRENGTH")
    print("="*70)
    print("\nProcesso in 3 fasi:")
    print("  1. Calcolo forza reparti (da statistiche giocatori)")
    print("  2. Calcolo produzione recente e storico Serie A")
    print("  3. Unificazione 40% recente, 30% reparti, 20% classifica, 10% storico")

    if args.refresh_team_stats:
        print("\n  0. Download dati FBref (opzionale, richiesto)")
    print()

    # Fase 0 (opzionale): Download dati FBref
    if args.refresh_team_stats:
        download_args = ['--history-count', str(args.history_count)]
        if args.seasons:
            download_args = ['--seasons'] + args.seasons

        success0 = run_script(
            'data/Calendario/download_team_stats.py',
            'Fase 0: Download statistiche squadre da FBref',
            extra_args=download_args
        )

        if not success0:
            print("\n⚠️  Download FBref fallito, proseguo con dati esistenti")

    # Verifica che i file di input esistano
    required_files = [
        'data/Calendario/team_strength.json'
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print("⚠️  ATTENZIONE: File mancanti:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nIl calcolo potrebbe essere incompleto.")
        print()

    # Fase 1: Calcolo reparti
    success1 = run_script(
        'scripts/calculate_department_strength.py',
        'Fase 1: Calcolo forza reparti da giocatori'
    )

    # Fase 2: Produzione recente e storico lungo Serie A
    success2 = run_script(
        'Aggiornamento_Fine_Stagione/calculate_team_strength.py',
        'Fase 2: Calcolo produzione recente e storico Serie A'
    )

    # Fase 3: Unificazione finale
    success3 = run_script(
        'scripts/unify_team_strength.py',
        'Fase 3: Unificazione finale della forza squadra'
    )

    # Riepilogo
    print("\n" + "="*70)
    if success1 and success2 and success3:
        print("✅ AGGIORNAMENTO COMPLETATO CON SUCCESSO!")
        print("="*70)
        print("\nFile aggiornato: data/Calendario/team_strength.json")
        print("\n💡 Note:")
        print("  • Giocatori senza statistiche sono stati ignorati")
        print("  • Formula: 40% produzione recente + 30% reparti + 20% classifica + 10% storico Serie A")
        print("  • L'app userà questi valori per calcolare difficoltà avversari")
        if args.refresh_team_stats:
            print("  • Dati FBref aggiornati")
    else:
        print("⚠️  AGGIORNAMENTO COMPLETATO CON AVVISI")
        print("="*70)
        print("\nAlcune fasi hanno generato errori/avvisi.")
        print("Verifica l'output sopra per dettagli.")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
