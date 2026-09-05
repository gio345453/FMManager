"""
Calcolo forza reparti (Difesa, Centrocampo, Attacco) basato su dati reali giocatori
Formula: normalizzazione min-max + media pesata → scala 1-10

Uso:
    python scripts/calculate_department_strength.py
    python scripts/calculate_department_strength.py --current-season-file data/stats/CURRENT_SEASON_2026_2027.csv
    python scripts/calculate_department_strength.py --stats-file data/stats/FM_STATS_202526.csv

DATI DISPONIBILI (da FM_STATS):
- Pv: Presenze (partite giocate)
- Mv: Media voto
- Fm: Fantamedia (media fantavoto)
- Gf: Gol fatti
- Gs: Gol subiti (portieri)
- Rp: Rigori parati
- Rc: Rigori calciati
- R+/R-: Rigori segnati/sbagliati
- Ass: Assist
- Amm: Ammonizioni
- Esp: Espulsioni
- Au: Autogol

NOTA: Dati completi (xG, xGA, possesso palla, etc.) non disponibili.
      Usiamo i dati disponibili per calcolare forza reparti.
"""
import pandas as pd
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Aggiungi root al path per importare src.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import find_current_season_file, find_stats_files, STATS_DIR


class TeamDepartmentStrengthCalculator:
    """Calcola forza reparti (Difesa, Centrocampo, Attacco) per squadre in CURRENT_SEASON"""

    def __init__(
        self,
        current_season_file: str | Path | None = None,
        stats_file: str | Path | None = None,
        output_file='data/Calendario/team_department_strength.json',
        min_presenze=3
    ):
        # Risolvi file dinamicamente se non specificati
        if current_season_file is None:
            resolved = find_current_season_file()
            if resolved is None:
                raise FileNotFoundError(
                    f"Nessun file CURRENT_SEASON trovato in {STATS_DIR}. "
                    "Specifica --current-season-file esplicitamente."
                )
            self.current_season_file = resolved
        else:
            self.current_season_file = Path(current_season_file)

        if stats_file is None:
            resolved_files = find_stats_files()
            if not resolved_files or 'recent' not in resolved_files:
                raise FileNotFoundError(
                    f"Nessun file FM_STATS recente trovato in {STATS_DIR}. "
                    "Specifica --stats-file esplicitamente."
                )
            self.stats_file = resolved_files['recent'][0]
        else:
            self.stats_file = Path(stats_file)

        self.output_file = Path(output_file)
        self.min_presenze = min_presenze

        print(f"📂 CURRENT_SEASON: {self.current_season_file}")
        print(f"📂 FM_STATS: {self.stats_file}")


        # Mapping ruoli → reparto
        self.role_mapping = {
            'Por': 'Portiere',  # Non incluso nei reparti
            'D': 'Difesa',
            'Dc': 'Difesa',
            'Dd': 'Difesa',
            'Ds': 'Difesa',
            'E': 'Difesa',
            'M': 'Centrocampo',
            'C': 'Centrocampo',
            'T': 'Centrocampo',
            'W': 'Attacco',
            'A': 'Attacco',
            'Pc': 'Attacco'
        }

        # Pesi per ogni reparto (somma = 1.0)
        self.weights = {
            'Difesa': {
                'media_voto': 0.40,      # Qualità individuale difensori
                'presenze': 0.20,        # Continuità dei titolari
                'gol_subiti_inv': 0.30,  # Solidità difensiva (meno gol = meglio)
                'amm_esp_inv': 0.10      # Disciplina (meno cartellini = meglio)
            },
            'Centrocampo': {
                'media_voto': 0.35,      # Qualità individuale centrocampisti
                'assist': 0.25,          # Creatività
                'gol': 0.20,             # Contributo offensivo
                'presenze': 0.20         # Continuità
            },
            'Attacco': {
                'fantamedia': 0.40,      # Rendimento fantacalcio (include bonus)
                'gol': 0.35,             # Efficacia sotto porta
                'assist': 0.15,          # Supporto compagni
                'presenze': 0.10         # Continuità
            }
        }

        # Numero giocatori da considerare per reparto (top N titolari)
        self.top_n = {
            'Difesa': 4,        # 4 difensori titolari
            'Centrocampo': 4,   # 4 centrocampisti
            'Attacco': 2        # 2 attaccanti
        }

    def load_current_season_teams(self) -> List[str]:
        """Carica lista squadre presenti in CURRENT_SEASON"""
        df = pd.read_csv(self.current_season_file, sep=';', encoding='utf-8')
        teams = df['Squadra'].unique().tolist()
        print(f"📋 Squadre in CURRENT_SEASON: {len(teams)}")
        return teams

    def load_player_stats(self) -> pd.DataFrame:
        """Carica statistiche giocatori e filtra quelli senza dati"""
        df = pd.read_csv(self.stats_file, sep=';', encoding='utf-8')

        # Pulisci BOM se presente
        df.columns = df.columns.str.replace('﻿', '')

        # Converti virgole in punti per campi numerici
        numeric_cols = ['Mv', 'Fm', 'Gf', 'Gs', 'Ass']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

        # Converti interi
        int_cols = ['Pv', 'Amm', 'Esp']
        for col in int_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # FILTRA giocatori senza statistiche significative
        # Ignora giocatori con meno di min_presenze partite
        initial_count = len(df)
        df = df[df['Pv'] >= self.min_presenze].copy()
        filtered_count = initial_count - len(df)

        print(f"📊 Giocatori caricati: {len(df)}")
        if filtered_count > 0:
            print(f"   ⚠️  Ignorati {filtered_count} giocatori senza statistiche (< {self.min_presenze} presenze)")

        return df

    def assign_department(self, role: str) -> str:
        """Assegna reparto in base al ruolo"""
        return self.role_mapping.get(role, 'Unknown')

    def calculate_team_department_stats(
        self,
        team: str,
        department: str,
        df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calcola statistiche aggregate per un reparto di una squadra
        Ignora giocatori senza statistiche (già filtrati in load_player_stats)

        Returns:
            dict con metriche aggregate del reparto
        """
        # Filtra giocatori della squadra e reparto
        team_players = df[df['Squadra'] == team].copy()
        team_players['Reparto'] = team_players['Rm'].apply(self.assign_department)
        dept_players = team_players[team_players['Reparto'] == department].copy()

        # Se non ci sono giocatori con statistiche sufficienti, ritorna valori nulli
        if len(dept_players) == 0:
            return {
                'media_voto': 0,
                'fantamedia': 0,
                'gol': 0,
                'assist': 0,
                'presenze': 0,
                'gol_subiti': 0,
                'amm_esp': 0,
                'num_players': 0
            }

        # Ordina per presenze e prendi top N (o meno se non ci sono abbastanza giocatori)
        n_players = min(self.top_n[department], len(dept_players))
        dept_players = dept_players.nlargest(n_players, 'Pv')

        # Calcola metriche aggregate
        stats = {
            'media_voto': dept_players['Mv'].mean(),
            'fantamedia': dept_players['Fm'].mean(),
            'gol': dept_players['Gf'].sum(),
            'assist': dept_players['Ass'].sum(),
            'presenze': dept_players['Pv'].mean(),
            'gol_subiti': dept_players['Gs'].sum() if department == 'Difesa' else 0,
            'amm_esp': (dept_players['Amm'].sum() + dept_players['Esp'].sum() * 2),
            'num_players': len(dept_players)
        }

        return stats

    def normalize_value(self, value: float, min_val: float, max_val: float, inverse: bool = False) -> float:
        """
        Normalizza valore su scala 0-1 con formula min-max

        Args:
            value: valore da normalizzare
            min_val: minimo del campionato
            max_val: massimo del campionato
            inverse: True per metriche "negative" (es. gol subiti)

        Returns:
            float: valore normalizzato [0, 1]
        """
        if max_val == min_val:
            return 0.5

        if inverse:
            # Per metriche negative: più basso è meglio
            normalized = (max_val - value) / (max_val - min_val)
        else:
            # Per metriche positive: più alto è meglio
            normalized = (value - min_val) / (max_val - min_val)

        # Clamp tra 0 e 1
        return max(0.0, min(1.0, normalized))

    def calculate_department_strength(
        self,
        teams: List[str],
        department: str,
        df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calcola forza del reparto per tutte le squadre

        Returns:
            dict: {squadra: punteggio_1_10}
        """
        print(f"\n{'='*60}")
        print(f"Calcolo forza reparto: {department.upper()}")
        print('='*60)

        # Raccogli statistiche per tutte le squadre
        all_stats = {}
        for team in teams:
            all_stats[team] = self.calculate_team_department_stats(team, department, df)

        # Trova min/max per normalizzazione
        metrics = list(all_stats.values())

        min_max = {}
        for key in ['media_voto', 'fantamedia', 'gol', 'assist', 'presenze', 'gol_subiti', 'amm_esp']:
            values = [m[key] for m in metrics if m[key] > 0]
            if values:
                min_max[key] = (min(values), max(values))
            else:
                min_max[key] = (0, 1)

        # Calcola punteggio pesato per ogni squadra
        strengths = {}

        for team, stats in all_stats.items():
            if stats['num_players'] == 0:
                strengths[team] = 5.0  # Valore medio se mancano dati
                continue

            # Normalizza metriche
            normalized = {}

            if department == 'Difesa':
                normalized['media_voto'] = self.normalize_value(
                    stats['media_voto'], *min_max['media_voto']
                )
                normalized['presenze'] = self.normalize_value(
                    stats['presenze'], *min_max['presenze']
                )
                normalized['gol_subiti_inv'] = self.normalize_value(
                    stats['gol_subiti'], *min_max['gol_subiti'], inverse=True
                )
                normalized['amm_esp_inv'] = self.normalize_value(
                    stats['amm_esp'], *min_max['amm_esp'], inverse=True
                )

            elif department == 'Centrocampo':
                normalized['media_voto'] = self.normalize_value(
                    stats['media_voto'], *min_max['media_voto']
                )
                normalized['assist'] = self.normalize_value(
                    stats['assist'], *min_max['assist']
                )
                normalized['gol'] = self.normalize_value(
                    stats['gol'], *min_max['gol']
                )
                normalized['presenze'] = self.normalize_value(
                    stats['presenze'], *min_max['presenze']
                )

            elif department == 'Attacco':
                normalized['fantamedia'] = self.normalize_value(
                    stats['fantamedia'], *min_max['fantamedia']
                )
                normalized['gol'] = self.normalize_value(
                    stats['gol'], *min_max['gol']
                )
                normalized['assist'] = self.normalize_value(
                    stats['assist'], *min_max['assist']
                )
                normalized['presenze'] = self.normalize_value(
                    stats['presenze'], *min_max['presenze']
                )

            # Calcola somma pesata
            weighted_sum = 0
            weights = self.weights[department]

            for metric, weight in weights.items():
                weighted_sum += normalized.get(metric, 0) * weight

            # Converti in scala 1-10
            strength = 1 + (9 * weighted_sum)
            strengths[team] = round(strength, 1)

            print(f"{team:15} → {strength:.1f}")

        return strengths

    def calculate_overall_strength(
        self,
        defense: Dict[str, float],
        midfield: Dict[str, float],
        attack: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Combina forza reparti in punteggio overall

        Returns:
            dict: {squadra: {'defense': X, 'midfield': Y, 'attack': Z, 'overall': W}}
        """
        teams = set(defense.keys()) | set(midfield.keys()) | set(attack.keys())

        result = {}
        for team in teams:
            def_val = defense.get(team, 5.0)
            mid_val = midfield.get(team, 5.0)
            att_val = attack.get(team, 5.0)

            # Overall: media pesata dei 3 reparti
            # Peso: Difesa 30%, Centrocampo 35%, Attacco 35%
            overall = (def_val * 0.30) + (mid_val * 0.35) + (att_val * 0.35)

            result[team] = {
                'defense': def_val,
                'midfield': mid_val,
                'attack': att_val,
                'overall': round(overall, 1)
            }

        return result

    def save_to_json(self, data: Dict):
        """Salva risultati in JSON"""
        # Ordina per overall decrescente
        sorted_data = dict(sorted(
            data.items(),
            key=lambda x: x[1]['overall'],
            reverse=True
        ))

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Dati salvati in: {self.output_file}")

    def generate_report(self, data: Dict):
        """Genera report finale"""
        print("\n" + "="*80)
        print("FORZA REPARTI - RIEPILOGO FINALE")
        print("="*80)
        print(f"{'Squadra':<15} {'Difesa':>8} {'Centro':>8} {'Attacco':>8} {'Overall':>8}")
        print("-"*80)

        for team, values in sorted(data.items(), key=lambda x: x[1]['overall'], reverse=True):
            print(f"{team:<15} {values['defense']:>8.1f} {values['midfield']:>8.1f} "
                  f"{values['attack']:>8.1f} {values['overall']:>8.1f}")

        print("-"*80)

        # Top 5 per reparto
        print("\n🛡️  TOP 5 DIFESA:")
        top_def = sorted(data.items(), key=lambda x: x[1]['defense'], reverse=True)[:5]
        for i, (team, vals) in enumerate(top_def, 1):
            print(f"   {i}. {team:<15} {vals['defense']:.1f}")

        print("\n⚙️  TOP 5 CENTROCAMPO:")
        top_mid = sorted(data.items(), key=lambda x: x[1]['midfield'], reverse=True)[:5]
        for i, (team, vals) in enumerate(top_mid, 1):
            print(f"   {i}. {team:<15} {vals['midfield']:.1f}")

        print("\n⚡ TOP 5 ATTACCO:")
        top_att = sorted(data.items(), key=lambda x: x[1]['attack'], reverse=True)[:5]
        for i, (team, vals) in enumerate(top_att, 1):
            print(f"   {i}. {team:<15} {vals['attack']:.1f}")

        print("\n⭐ TOP 5 OVERALL:")
        top_ovr = sorted(data.items(), key=lambda x: x[1]['overall'], reverse=True)[:5]
        for i, (team, vals) in enumerate(top_ovr, 1):
            print(f"   {i}. {team:<15} {vals['overall']:.1f}")

    def run(self):
        """Esegue calcolo completo"""
        print("="*80)
        print("CALCOLO FORZA REPARTI DA STATISTICHE REALI GIOCATORI")
        print("="*80)
        print("\nMetodo: Normalizzazione min-max + Media pesata → Scala 1-10")
        print("Reparti: Difesa (top 4), Centrocampo (top 4), Attacco (top 2)")
        print(f"Filtro: Ignora giocatori con < {self.min_presenze} presenze")

        # Carica dati
        teams = self.load_current_season_teams()
        df = self.load_player_stats()

        # Verifica che ci siano dati sufficienti
        if len(df) == 0:
            print("\n❌ ERRORE: Nessun giocatore con statistiche disponibili!")
            print("   Verifica che FM_STATS sia aggiornato con dati della stagione corrente.")
            return

        # Calcola forza per ogni reparto
        defense = self.calculate_department_strength(teams, 'Difesa', df)
        midfield = self.calculate_department_strength(teams, 'Centrocampo', df)
        attack = self.calculate_department_strength(teams, 'Attacco', df)

        # Combina in overall
        result = self.calculate_overall_strength(defense, midfield, attack)

        # Salva file
        self.save_to_json(result)

        # Mostra report
        self.generate_report(result)

        print("\n" + "="*80)
        print("✅ COMPLETATO!")
        print("="*80)
        print("\nFile generato: team_department_strength.json")
        print("Usa questo file per analisi avversari e rotazione portieri.")
        print("\n💡 I giocatori senza statistiche sono stati automaticamente ignorati.")


def main():
    parser = argparse.ArgumentParser(
        description='Calcola forza reparti da statistiche giocatori',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--current-season-file',
        help='File CURRENT_SEASON CSV (default: risolto automaticamente)'
    )
    parser.add_argument(
        '--stats-file',
        help='File FM_STATS CSV (default: stagione più recente)'
    )
    parser.add_argument(
        '--output',
        default='data/Calendario/team_department_strength.json',
        help='File output JSON (default: data/Calendario/team_department_strength.json)'
    )
    parser.add_argument(
        '--min-presenze',
        type=int,
        default=3,
        help='Minimo presenze per considerare un giocatore (default: 3)'
    )

    args = parser.parse_args()

    try:
        calculator = TeamDepartmentStrengthCalculator(
            current_season_file=args.current_season_file,
            stats_file=args.stats_file,
            output_file=args.output,
            min_presenze=args.min_presenze
        )
        calculator.run()
    except FileNotFoundError as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
