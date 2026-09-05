"""
Goalkeeper rotation analyzer - Trova migliori abbinamenti portieri
Basato su fixture difficulty, casa/trasferta e giornata corrente
"""
from typing import List, Dict, Tuple, Optional
from src.data.fixture_difficulty import get_fixture_calculator
from src.data.settings_manager import get_current_matchday
from itertools import combinations


class GoalkeeperRotationAnalyzer:
    """Analizza rotazioni portieri per trovare migliori abbinamenti"""

    def __init__(self):
        self.fixture_calc = get_fixture_calculator()

    def analyze_goalkeeper_rotation(
        self,
        goalkeepers: List[Dict],
        from_matchday: Optional[int] = None
    ) -> Dict:
        """
        Analizza rotazione portieri per trovare miglior abbinamento

        Args:
            goalkeepers: Lista 2-3 portieri con {id, name, team}
            from_matchday: Giornata iniziale (None = da settings)

        Returns:
            Dict con griglia, statistiche e suggerimenti
        """
        if from_matchday is None:
            from_matchday = get_current_matchday()

        # Genera griglia per ogni portiere
        grids = []
        for gk in goalkeepers:
            grid = self._generate_goalkeeper_grid(
                gk['team'],
                from_matchday
            )
            grids.append({
                'goalkeeper_id': gk['id'],
                'goalkeeper_name': gk['name'],
                'team': gk['team'],
                'grid': grid
            })

        # Analizza migliori combinazioni
        combinations_analysis = self._analyze_combinations(grids, from_matchday)

        return {
            'grids': grids,
            'combinations': combinations_analysis,
            'from_matchday': from_matchday,
            'total_matchdays': 38 - from_matchday + 1
        }

    def _generate_goalkeeper_grid(
        self,
        team: str,
        from_matchday: int
    ) -> List[Dict]:
        """
        Genera griglia 38 giornate per un portiere

        Returns:
            Lista di 38 dict con matchday, opponent, is_home, difficulty, color
        """
        grid = []

        for matchday in range(from_matchday, 39):
            fixture = self.fixture_calc.get_fixture_for_team(team, matchday)

            if not fixture:
                # Nessuna partita trovata
                grid.append({
                    'matchday': matchday,
                    'opponent': '-',
                    'is_home': None,
                    'difficulty_score': None,
                    'color': 'gray',
                    'playable': False
                })
                continue

            opponent = fixture['opponent']
            is_home = fixture['is_home']

            difficulty_data = self.fixture_calc.calculate_difficulty_modifiers(team, matchday, 'P')
            difficulty = difficulty_data['difficulty_score']

            # Determina colore
            # Verde: facile (<4.5) o casa contro medio (4.5-6.5)
            # Giallo: medio (4.5-7.0)
            # Rosso: difficile (>7.0)
            if difficulty < 4.5:
                color = 'green'
            elif difficulty < 7.0:
                color = 'yellow'
            else:
                color = 'red'

            # Bonus verde per casa contro medio
            if is_home and 4.5 <= difficulty < 6.5:
                color = 'green'

            grid.append({
                'matchday': matchday,
                'opponent': opponent,
                'is_home': is_home,
                'difficulty_score': round(difficulty, 2),
                'color': color,
                'playable': True
            })

        return grid

    def _analyze_combinations(
        self,
        grids: List[Dict],
        from_matchday: int
    ) -> Dict:
        """
        Analizza tutte le combinazioni possibili di rotazione

        Per ogni giornata, sceglie il portiere con partita più facile
        """
        num_goalkeepers = len(grids)
        total_matchdays = 38 - from_matchday + 1

        # Per ogni giornata, trova portiere migliore
        best_choice_per_matchday = []

        for matchday in range(from_matchday, 39):
            matchday_idx = matchday - from_matchday

            # Trova portiere con partita più facile questa giornata
            best_gk = None
            best_difficulty = float('inf')
            best_color = None

            for grid_data in grids:
                cell = grid_data['grid'][matchday_idx]

                if not cell['playable']:
                    continue

                difficulty = cell['difficulty_score']

                # Priorità: verde > giallo > rosso
                # A parità di colore, prendi difficulty minore
                priority = {
                    'green': 0,
                    'yellow': 1,
                    'red': 2,
                    'gray': 3
                }

                cell_priority = priority[cell['color']]

                if (cell_priority < priority.get(best_color, 3) or
                    (cell_priority == priority.get(best_color, 3) and difficulty < best_difficulty)):
                    best_gk = grid_data['goalkeeper_name']
                    best_difficulty = difficulty
                    best_color = cell['color']

            best_choice_per_matchday.append({
                'matchday': matchday,
                'goalkeeper': best_gk,
                'difficulty': best_difficulty if best_difficulty != float('inf') else None,
                'color': best_color
            })

        # Calcola statistiche aggregate
        green_count = sum(1 for c in best_choice_per_matchday if c['color'] == 'green')
        yellow_count = sum(1 for c in best_choice_per_matchday if c['color'] == 'yellow')
        red_count = sum(1 for c in best_choice_per_matchday if c['color'] == 'red')

        # Conta presenze per portiere
        goalkeeper_usage = {}
        for choice in best_choice_per_matchday:
            gk = choice['goalkeeper']
            if gk:
                goalkeeper_usage[gk] = goalkeeper_usage.get(gk, 0) + 1

        # Calcola OVERALL ABBINAMENTO (0-10)
        overall_rating = self._calculate_overall_rating(
            best_choice_per_matchday,
            total_matchdays
        )

        return {
            'best_choice_per_matchday': best_choice_per_matchday,
            'green_matchdays': green_count,
            'yellow_matchdays': yellow_count,
            'red_matchdays': red_count,
            'goalkeeper_usage': goalkeeper_usage,
            'total_matchdays': total_matchdays,
            'overall_rating': overall_rating  # NUOVO!
        }

    def _calculate_overall_rating(
        self,
        best_choices: List[Dict],
        total_matchdays: int
    ) -> float:
        """
        Calcola overall rating abbinamento (0-10) basato su:
        - Percentuale partite verdi (peso 50%)
        - Difficoltà media partite verdi (peso 30%)
        - Assenza partite rosse (peso 20%)

        Returns:
            float: Rating 0-10 (10 = perfetto)
        """
        if total_matchdays == 0:
            return 5.0

        # Conta colori
        green_count = sum(1 for c in best_choices if c['color'] == 'green')
        yellow_count = sum(1 for c in best_choices if c['color'] == 'yellow')
        red_count = sum(1 for c in best_choices if c['color'] == 'red')

        # Fattore 1: Percentuale partite verdi (0-10)
        green_percentage = green_count / total_matchdays
        green_score = green_percentage * 10

        # Fattore 2: Qualità partite verdi - difficoltà media (0-10)
        # Difficoltà verde ideale: < 3.0
        # Difficoltà verde accettabile: < 4.5
        green_difficulties = [
            c['difficulty'] for c in best_choices
            if c['color'] == 'green' and c['difficulty'] is not None
        ]

        if green_difficulties:
            avg_green_difficulty = sum(green_difficulties) / len(green_difficulties)
            # Normalizza: 1.0 (ottimo) → 10, 4.5 (limite verde) → 5, >6.0 (pessimo) → 0
            if avg_green_difficulty <= 1.0:
                quality_score = 10.0
            elif avg_green_difficulty <= 3.0:
                # Da 1.0 a 3.0 → da 10 a 7
                quality_score = 10 - ((avg_green_difficulty - 1.0) / 2.0) * 3
            elif avg_green_difficulty <= 4.5:
                # Da 3.0 a 4.5 → da 7 a 5
                quality_score = 7 - ((avg_green_difficulty - 3.0) / 1.5) * 2
            else:
                # > 4.5 (non dovrebbe succedere con partite verdi)
                quality_score = max(0, 5 - (avg_green_difficulty - 4.5))
        else:
            # Nessuna partita verde → qualità 0
            quality_score = 0.0

        # Fattore 3: Penalità partite rosse (0-10)
        red_percentage = red_count / total_matchdays
        red_penalty_score = max(0, 10 - (red_percentage * 20))  # -2 punti per ogni 10% rosso

        # Media pesata
        overall = (
            green_score * 0.50 +      # 50% importanza partite verdi
            quality_score * 0.30 +    # 30% importanza qualità verdi
            red_penalty_score * 0.20  # 20% importanza evitare rossi
        )

        return round(overall, 1)


# Singleton globale
_rotation_analyzer = None


def get_rotation_analyzer() -> GoalkeeperRotationAnalyzer:
    """Ottiene istanza singleton analyzer"""
    global _rotation_analyzer
    if _rotation_analyzer is None:
        _rotation_analyzer = GoalkeeperRotationAnalyzer()
    return _rotation_analyzer
