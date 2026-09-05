"""
Modulo per la gestione delle statistiche delle squadre
Calcola statistiche aggregate dai dati reali della stagione 2025-2026
"""
import pandas as pd
from src.data.stats_loader import StatsLoader


# Classifica reale Serie A 2025-2026 da FBref/Sky Sport
CLASSIFICA_REALE_2025_26 = {
    'Inter': {'pos': 1, 'pts': 87, 'gf': 89, 'gs': 35},
    'Napoli': {'pos': 2, 'pts': 76, 'gf': 58, 'gs': 36},
    'Roma': {'pos': 3, 'pts': 73, 'gf': 59, 'gs': 31},
    'Como': {'pos': 4, 'pts': 71, 'gf': 65, 'gs': 29},
    'Milan': {'pos': 5, 'pts': 70, 'gf': 53, 'gs': 35},
    'Juventus': {'pos': 6, 'pts': 69, 'gf': 61, 'gs': 34},
    'Atalanta': {'pos': 7, 'pts': 59, 'gf': 51, 'gs': 36},
    'Bologna': {'pos': 8, 'pts': 56, 'gf': 49, 'gs': 46},
    'Lazio': {'pos': 9, 'pts': 54, 'gf': 41, 'gs': 40},
    'Udinese': {'pos': 10, 'pts': 50, 'gf': 45, 'gs': 48},
    'Sassuolo': {'pos': 11, 'pts': 49, 'gf': 46, 'gs': 50},
    'Torino': {'pos': 12, 'pts': 45, 'gf': 44, 'gs': 63},
    'Parma': {'pos': 13, 'pts': 45, 'gf': 28, 'gs': 46},
    'Cagliari': {'pos': 14, 'pts': 43, 'gf': 40, 'gs': 53},
    'Fiorentina': {'pos': 15, 'pts': 42, 'gf': 41, 'gs': 50},
    'Genoa': {'pos': 16, 'pts': 41, 'gf': 41, 'gs': 51},
    'Lecce': {'pos': 17, 'pts': 38, 'gf': 28, 'gs': 50},
    'Cremonese': {'pos': 18, 'pts': 34, 'gf': 32, 'gs': 57},
    'Verona': {'pos': 19, 'pts': 21, 'gf': 25, 'gs': 59},
    'Pisa': {'pos': 20, 'pts': 18, 'gf': 26, 'gs': 70},
}

# Alias per stagione corrente (aggiornare ogni anno)
CLASSIFICA_REALE_CURRENT_SEASON = CLASSIFICA_REALE_2025_26


class TeamStatsManager:
    """Gestisce le statistiche aggregate per squadra dalla stagione 2025-2026"""

    def __init__(self, players_df=None):
        """
        Args:
            players_df: DataFrame con tutti i giocatori (non usato, carica da file)
        """
        self.stats_loader = StatsLoader()
        self.season_2025_data = None
        self._load_season_2025_data()

    def _load_season_2025_data(self):
        """Carica i dati reali della stagione 2025-2026 (stagione più recente)"""
        stats_data = self.stats_loader.load_all_stats()

        if stats_data and 'recent' in stats_data:
            # 'recent' contiene {'df': DataFrame, 'weight': float}
            self.season_2025_data = stats_data['recent']['df'].reset_index()

            # Converti colonne numeriche
            numeric_cols = ['Pv', 'Mv', 'Fm', 'Gf', 'Gs', 'Rp', 'Rc', 'R+', 'R-', 'Ass', 'Amm', 'Esp', 'Au']
            for col in numeric_cols:
                if col in self.season_2025_data.columns:
                    self.season_2025_data[col] = pd.to_numeric(self.season_2025_data[col], errors='coerce')

    def get_team_stats(self, team_name):
        """
        Ottieni statistiche complete per una squadra dalla stagione 2025-2026

        Args:
            team_name: Nome della squadra

        Returns:
            dict con tutte le statistiche della squadra
        """
        if self.season_2025_data is None or self.season_2025_data.empty:
            return None

        # Filtra giocatori della squadra nella stagione 2025-26
        team_players = self.season_2025_data[self.season_2025_data['Squadra'] == team_name]

        # Usa i dati reali della classifica se disponibili
        # Inizializza league_data con dati classifica se disponibili
        if team_name in CLASSIFICA_REALE_2025_26:
            real_data = CLASSIFICA_REALE_2025_26[team_name]
            league_data = {
                'posizione': real_data['pos'],
                'punti': real_data['pts'],
                'gol_fatti': real_data['gf'],
                'gol_subiti': real_data['gs'],
                'differenza_reti': real_data['gf'] - real_data['gs']
            }
        else:
            # Dati non trovati nella classifica reale
            league_data = {
                'posizione': None,
                'punti': None,
                'gol_fatti': None,
                'gol_subiti': None,
                'differenza_reti': None
            }

        if team_players.empty:
            # Usa solo dati classifica
            return {
                'squadra': team_name,
                'classifica': league_data,
                'giocatori_chiave': {
                    'fm': {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'fm': 0, 'pv': 0},
                    'gol': {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'gol': 0, 'pv': 0},
                    'assist': {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'assist': 0, 'pv': 0}
                },
                'reparti': {
                    'dettaglio': {r: {'giocatori': 0, 'fm_media': 0.0, 'overall_media': 0.0} for r in ['P', 'D', 'C', 'A']},
                    'reparto_piu_forte': {'reparto': 'N/A', 'fm_media': 0.0}
                },
                'totale_giocatori': 0
            }

        # Calcola i 3 giocatori chiave
        key_players = self._calculate_key_players(team_players)

        # Reparto con FM più alta (media per reparto)
        department_stats = self._calculate_department_stats(team_players)

        return {
            'squadra': team_name,
            'classifica': league_data,
            'giocatori_chiave': key_players,
            'reparti': department_stats,
            'totale_giocatori': len(team_players)
        }

    def _calculate_key_players(self, team_players):
        """
        Calcola i 3 giocatori chiave: FM più alta (con 70% presenze), più gol, più assist

        Args:
            team_players: DataFrame con i giocatori della squadra

        Returns:
            dict con i 3 giocatori chiave
        """
        # Filtra giocatori con almeno 70% delle partite (38 * 0.7 = 26.6 -> 27 partite)
        min_presenze = 27
        players_qualified = team_players[team_players['Pv'] >= min_presenze]

        # Giocatore con FM più alta (tra quelli qualificati)
        if not players_qualified.empty:
            fm_player = players_qualified.nlargest(1, 'Fm').iloc[0]
            fm_key = {
                'id': fm_player['Id'],
                'nome': fm_player['Nome'],
                'ruolo': fm_player['R'],
                'fm': round(fm_player['Fm'], 2),
                'pv': int(fm_player['Pv'])
            }
        else:
            fm_key = {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'fm': 0, 'pv': 0}

        # Giocatore con più gol (tra tutti, non solo qualificati)
        if not team_players.empty and team_players['Gf'].max() > 0:
            gol_player = team_players.nlargest(1, 'Gf').iloc[0]
            gol_key = {
                'id': gol_player['Id'],
                'nome': gol_player['Nome'],
                'ruolo': gol_player['R'],
                'gol': int(gol_player['Gf']),
                'pv': int(gol_player['Pv'])
            }
        else:
            gol_key = {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'gol': 0, 'pv': 0}

        # Giocatore con più assist (tra tutti, non solo qualificati)
        if not team_players.empty and team_players['Ass'].max() > 0:
            ass_player = team_players.nlargest(1, 'Ass').iloc[0]
            ass_key = {
                'id': ass_player['Id'],
                'nome': ass_player['Nome'],
                'ruolo': ass_player['R'],
                'assist': int(ass_player['Ass']),
                'pv': int(ass_player['Pv'])
            }
        else:
            ass_key = {'id': None, 'nome': 'N/A', 'ruolo': 'N/A', 'assist': 0, 'pv': 0}

        return {
            'fm': fm_key,
            'gol': gol_key,
            'assist': ass_key
        }

    def _calculate_department_stats(self, team_players):
        """
        Calcola statistiche per reparto (P, D, C, A) dalla stagione 2025-26
        Considera solo giocatori con almeno 10 presenze per la FM media

        Args:
            team_players: DataFrame con i giocatori della squadra

        Returns:
            dict con statistiche per reparto
        """
        departments = {}
        min_presenze = 10

        for dept in ['P', 'D', 'C', 'A']:
            dept_players = team_players[team_players['R'] == dept]

            if dept_players.empty:
                departments[dept] = {
                    'giocatori': 0,
                    'fm_media': 0.0,
                    'overall_media': 0.0
                }
            else:
                # Filtra giocatori con almeno 10 presenze per FM media
                qualified_players = dept_players[dept_players['Pv'] >= min_presenze]

                if qualified_players.empty:
                    fm_media = 0.0
                else:
                    fm_media = qualified_players['Fm'].mean()

                # Calcola Overall media se disponibile
                if 'Overall' in dept_players.columns:
                    overall_values = pd.to_numeric(dept_players['Overall'], errors='coerce')
                    overall_media = overall_values.mean() if not overall_values.isna().all() else 0.0
                else:
                    overall_media = fm_media  # Usa FM come proxy

                departments[dept] = {
                    'giocatori': len(dept_players),
                    'fm_media': round(fm_media, 2),
                    'overall_media': round(overall_media, 2)
                }

        # Trova reparto più forte (FM media più alta)
        best_dept = max(departments.items(), key=lambda x: x[1]['fm_media'])

        return {
            'dettaglio': departments,
            'reparto_piu_forte': {
                'reparto': best_dept[0],
                'fm_media': best_dept[1]['fm_media']
            }
        }

    def get_all_teams_summary(self):
        """
        Ottieni un riepilogo di tutte le squadre dalla stagione corrente

        Returns:
            list di dict con statistiche base per ogni squadra
        """
        # Usa la classifica reale come base
        summary = []

        for team_name, data in CLASSIFICA_REALE_CURRENT_SEASON.items():
            stats = self.get_team_stats(team_name)
            if stats:
                # Formatta i giocatori chiave per il summary
                fm_player = stats['giocatori_chiave']['fm']['nome']
                gol_player = stats['giocatori_chiave']['gol']['nome']
                ass_player = stats['giocatori_chiave']['assist']['nome']

                summary.append({
                    'squadra': team_name,
                    'posizione': data['pos'],
                    'punti': data['pts'],
                    'gol_fatti': data['gf'],
                    'gol_subiti': data['gs'],
                    'giocatore_chiave': f"{fm_player} (FM)",
                    'capocannoniere': f"{gol_player} ({stats['giocatori_chiave']['gol']['gol']} gol)",
                    'top_assist': f"{ass_player} ({stats['giocatori_chiave']['assist']['assist']} ass)",
                    'reparto_forte': stats['reparti']['reparto_piu_forte']['reparto']
                })

        # Ordina per posizione reale
        summary.sort(key=lambda x: x['posizione'])
        return summary

    def update_players_data(self, players_df):
        """
        Aggiorna il DataFrame dei giocatori (non usato, usa dati da file)

        Args:
            players_df: Nuovo DataFrame con i giocatori
        """
        pass  # Non necessario, usa dati dalla stagione corrente
