"""
Sistema completo fixture difficulty per proiezioni giornata per giornata
Replica logica FisherTiger con coefficienti casa/trasferta e forza avversario
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from src.data.team_strength_data import clamp_strength, role_strength, unwrap_teams


# Coefficienti fixture difficulty (da FisherTiger)
FIXTURE_HOME_PLAY_EFFECT = 0.025      # +2.5% probabilità giocare in casa
FIXTURE_HOME_VOTE_EFFECT = 0.035      # +3.5% voto medio in casa
FIXTURE_HOME_BONUS_EFFECT = 0.045     # +4.5% bonus atteso in casa

FIXTURE_STRENGTH_PLAY_EFFECT = 0.009  # +0.9% prob per punto forza avversario debole
FIXTURE_DEFENCE_VOTE_EFFECT = 0.018   # +1.8% voto per punto difesa avversaria debole
FIXTURE_ATTACK_BONUS_EFFECT = 0.055   # +5.5% bonus per punto attacco avversario debole


def get_current_matchday_from_settings() -> int:
    """
    Ottiene la giornata corrente dalle impostazioni

    Returns:
        int: Giornata corrente (1-38), default 1 se non disponibile
    """
    try:
        from src.data.settings_manager import get_current_matchday
        return get_current_matchday()
    except Exception:
        return 1  # Fallback


class FixtureDifficultyCalculator:
    """Calcola difficulty e proiezioni per ogni giornata"""

    def __init__(self, calendario_path: Optional[Path] = None,
                 team_strength_path: Optional[Path] = None):
        """
        Args:
            calendario_path: Path al calendario JSON
            team_strength_path: Path ai coefficienti forza squadre
        """
        self.base_dir = Path(__file__).parent.parent.parent / 'data' / 'Calendario'

        if calendario_path is None:
            # Cerca ultimo calendario disponibile
            calendario_path = self._find_latest_calendario()

        if team_strength_path is None:
            team_strength_path = self.base_dir / 'team_strength.json'

        self.calendario = self._load_calendario(calendario_path)
        self.team_strength = self._load_team_strength(team_strength_path)

        # Cache per lookup veloce
        self._fixture_cache = {}
        self._build_fixture_cache()

    def _find_latest_calendario(self) -> Optional[Path]:
        """Trova l'ultimo calendario disponibile"""
        # Prima cerca calendario.json (standard)
        standard_calendario = self.base_dir / 'calendario.json'
        if standard_calendario.exists():
            return standard_calendario

        # Fallback: cerca vecchi file calendario_seriea_*.json
        calendario_files = list(self.base_dir.glob('calendario_seriea_*.json'))

        if not calendario_files:
            return None

        # Ordina per data modifica (più recente)
        return max(calendario_files, key=lambda p: p.stat().st_mtime)

    def _load_calendario(self, path: Optional[Path]) -> Dict:
        """Carica calendario da JSON"""
        if path is None or not path.exists():
            print(f"⚠ Calendario non trovato: {path}")
            return {'matches': []}

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✓ Calendario caricato: {len(data.get('matches', []))} partite")
        return data

    def _load_team_strength(self, path: Path) -> Dict:
        """Carica coefficienti forza squadre"""
        if not path.exists():
            print(f"⚠ Team strength non trovato: {path}")
            return {'teams': {}}

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        teams = unwrap_teams(data)
        print(f"✓ Team strength caricato: {len(teams)} squadre")
        return {**data, 'teams': teams}

    def _opponent_strength(self, opponent: str) -> Dict[str, float]:
        return self.team_strength.get('teams', {}).get(opponent, {})

    @staticmethod
    def _difficulty_score(opponent_strength: Dict[str, float], is_home: bool, role: Optional[str] = None) -> float:
        difficulty = role_strength(opponent_strength, role)
        difficulty *= 0.85 if is_home else 1.15
        return max(1.0, min(10.0, difficulty))

    def _build_fixture_cache(self):
        """Costruisce cache per lookup veloce giornata/squadra"""
        self._fixture_cache = {}

        for match in self.calendario.get('matches', []):
            matchday = match.get('matchday')
            home_team = match.get('home_team')
            away_team = match.get('away_team')

            if not all([matchday, home_team, away_team]):
                continue

            # Cache per squadra casa
            key_home = (matchday, home_team)
            self._fixture_cache[key_home] = {
                'opponent': away_team,
                'is_home': True,
                'match': match
            }

            # Cache per squadra trasferta
            key_away = (matchday, away_team)
            self._fixture_cache[key_away] = {
                'opponent': home_team,
                'is_home': False,
                'match': match
            }

    def get_fixture_for_team(self, team: str, matchday: int) -> Optional[Dict]:
        """
        Ottiene fixture per squadra in giornata specifica

        Returns:
            Dict con opponent, is_home, match o None
        """
        return self._fixture_cache.get((matchday, team))

    def calculate_difficulty_modifiers(self, team: str, matchday: int,
                                       role: str) -> Dict[str, float]:
        """
        Calcola modificatori difficulty per squadra in giornata

        Args:
            team: Nome squadra giocatore
            matchday: Numero giornata (1-38)
            role: Ruolo giocatore (P/D/C/A)

        Returns:
            Dict con play_modifier, vote_modifier, bonus_modifier
        """
        fixture = self.get_fixture_for_team(team, matchday)

        if not fixture:
            # Nessuna fixture trovata, ritorna neutral
            return {
                'play_modifier': 1.0,
                'vote_modifier': 1.0,
                'bonus_modifier': 1.0,
                'difficulty_score': 5.0  # neutral
            }

        opponent = fixture['opponent']
        is_home = fixture['is_home']

        # Ottieni forza avversario
        opponent_strength = self._opponent_strength(opponent)
        opponent_defense = clamp_strength(opponent_strength.get('defense'))
        opponent_attack = clamp_strength(opponent_strength.get('attack'))
        opponent_overall = clamp_strength(opponent_strength.get('overall'))
        opponent_midfield = clamp_strength(opponent_strength.get('midfield'), default=opponent_overall)
        role_difficulty = role_strength(opponent_strength, role)

        # Calcola modificatori
        play_modifier = 1.0
        vote_modifier = 1.0
        bonus_modifier = 1.0

        # Effetto casa/trasferta
        if is_home:
            play_modifier += FIXTURE_HOME_PLAY_EFFECT
            vote_modifier += FIXTURE_HOME_VOTE_EFFECT
            bonus_modifier += FIXTURE_HOME_BONUS_EFFECT

        # Ogni ruolo usa il reparto avversario che gli si oppone direttamente.
        strength_diff = 10.0 - role_difficulty
        play_modifier += strength_diff * FIXTURE_STRENGTH_PLAY_EFFECT
        vote_modifier += strength_diff * FIXTURE_DEFENCE_VOTE_EFFECT
        if role in ['A', 'C']:
            bonus_modifier += strength_diff * FIXTURE_ATTACK_BONUS_EFFECT

        difficulty_score = self._difficulty_score(opponent_strength, is_home, role)

        return {
            'play_modifier': play_modifier,
            'vote_modifier': vote_modifier,
            'bonus_modifier': bonus_modifier,
            'difficulty_score': difficulty_score,
            'role_difficulty_score': difficulty_score,
            'opponent': opponent,
            'is_home': is_home,
            'opponent_attack': opponent_attack,
            'opponent_defense': opponent_defense,
            'opponent_overall': opponent_overall,
            'opponent_midfield': opponent_midfield
        }

    def calculate_player_projections_per_matchday(
        self,
        team: str,
        role: str,
        base_p_gioca: float,
        base_voto_mean: float,
        base_voto_std: float,
        base_bonus: float,
        matchdays: int = 38
    ) -> List[Dict]:
        """
        Calcola proiezioni per ogni giornata (completo FisherTiger style)

        Args:
            team: Squadra giocatore
            role: Ruolo (P/D/C/A)
            base_p_gioca: Probabilità base giocare
            base_voto_mean: Voto medio base
            base_voto_std: Deviazione standard voto base
            base_bonus: Bonus medio base
            matchdays: Numero giornate (default 38)

        Returns:
            Lista di 38 dict con p_gioca, voto_mean, voto_std, bonus per giornata
        """
        projections = []

        for matchday in range(1, matchdays + 1):
            difficulty = self.calculate_difficulty_modifiers(team, matchday, role)

            # Applica modificatori
            p_gioca = base_p_gioca * difficulty['play_modifier']
            p_gioca = max(0.0, min(1.0, p_gioca))  # Clamp 0-1

            voto_mean = base_voto_mean * difficulty['vote_modifier']
            voto_mean = max(4.0, min(10.0, voto_mean))  # Clamp 4-10

            bonus = base_bonus * difficulty['bonus_modifier']

            projections.append({
                'matchday': matchday,
                'p_gioca': round(p_gioca, 4),
                'voto_mean': round(voto_mean, 3),
                'voto_std': round(base_voto_std, 3),  # Std rimane costante
                'bonus': round(bonus, 3),
                'difficulty_score': round(difficulty['difficulty_score'], 2),
                'role_difficulty_score': round(difficulty['role_difficulty_score'], 2),
                'opponent': difficulty.get('opponent', 'N/A'),
                'is_home': difficulty.get('is_home', True),
                'opponent_attack': difficulty.get('opponent_attack', 5.0),
                'opponent_defense': difficulty.get('opponent_defense', 5.0)
            })

        return projections

    def calculate_seasonal_average_modifiers(
        self,
        team: str,
        role: str,
        matchdays: int = 38
    ) -> Dict[str, float]:
        """
        Calcola modificatori medi stagionali (per calcoli semplificati)

        Returns:
            Dict con play_avg, vote_avg, bonus_avg
        """
        total_play = 0.0
        total_vote = 0.0
        total_bonus = 0.0

        for matchday in range(1, matchdays + 1):
            difficulty = self.calculate_difficulty_modifiers(team, matchday, role)
            total_play += difficulty['play_modifier']
            total_vote += difficulty['vote_modifier']
            total_bonus += difficulty['bonus_modifier']

        return {
            'play_avg': total_play / matchdays,
            'vote_avg': total_vote / matchdays,
            'bonus_avg': total_bonus / matchdays
        }

    def get_next_5_fixtures(
        self,
        team: str,
        current_matchday: Optional[int] = None,
        role: Optional[str] = None,
    ) -> List[Dict]:
        """
        Ottiene prossime 5 partite con difficulty

        Utile per UI "prossimi avversari"

        Args:
            team: Nome squadra
            current_matchday: Giornata corrente (se None, usa dalle settings)

        Returns:
            Lista di max 5 dict con fixture info
        """
        if current_matchday is None:
            current_matchday = get_current_matchday_from_settings()

        fixtures = []

        for offset in range(5):
            matchday = current_matchday + offset
            if matchday > 38:
                break

            fixture = self.get_fixture_for_team(team, matchday)
            if not fixture:
                continue

            opponent = fixture['opponent']
            is_home = fixture['is_home']

            opponent_strength = self._opponent_strength(opponent)
            difficulty_score = self._difficulty_score(opponent_strength, is_home, role)

            fixtures.append({
                'matchday': matchday,
                'opponent': opponent,
                'is_home': is_home,
                'difficulty_score': round(difficulty_score, 2),
                'opponent_attack': clamp_strength(opponent_strength.get('attack')),
                'opponent_defense': clamp_strength(opponent_strength.get('defense')),
                'opponent_overall': clamp_strength(opponent_strength.get('overall')),
                'opponent_midfield': clamp_strength(opponent_strength.get('midfield'), default=5.0)
            })

        return fixtures

    def get_fixture_summary(
        self,
        team: str,
        matchdays: int = 38,
        from_matchday: Optional[int] = None,
        role: Optional[str] = None,
    ) -> Dict:
        """
        Riassunto difficulty stagionale per squadra

        Args:
            team: Nome squadra
            matchdays: Numero totale giornate (default 38)
            from_matchday: Giornata iniziale (se None, usa dalle settings per "rimanenti")

        Returns:
            Dict con easy_count, medium_count, hard_count, avg_difficulty, remaining
        """
        if from_matchday is None:
            from_matchday = get_current_matchday_from_settings()

        easy_count = 0
        medium_count = 0
        hard_count = 0
        total_difficulty = 0.0
        fixtures_counted = 0

        for matchday in range(from_matchday, matchdays + 1):
            fixture = self.get_fixture_for_team(team, matchday)
            if not fixture:
                continue

            opponent = fixture['opponent']
            is_home = fixture['is_home']

            opponent_strength = self._opponent_strength(opponent)
            difficulty = self._difficulty_score(opponent_strength, is_home, role)

            total_difficulty += difficulty
            fixtures_counted += 1

            if difficulty < 4.5:
                easy_count += 1
            elif difficulty < 7.0:
                medium_count += 1
            else:
                hard_count += 1

        return {
            'easy_fixtures': easy_count,
            'medium_fixtures': medium_count,
            'hard_fixtures': hard_count,
            'avg_difficulty': round(total_difficulty / fixtures_counted, 2) if fixtures_counted > 0 else 5.0,
            'remaining_fixtures': fixtures_counted,
            'from_matchday': from_matchday
        }


# Singleton globale
_fixture_calculator = None


def get_fixture_calculator() -> FixtureDifficultyCalculator:
    """Ottieni istanza singleton del calculator"""
    global _fixture_calculator

    if _fixture_calculator is None:
        _fixture_calculator = FixtureDifficultyCalculator()

    return _fixture_calculator


def invalidate_fixture_calculator() -> None:
    """Forza il ricaricamento del calendario alla prossima richiesta."""
    global _fixture_calculator
    _fixture_calculator = None


def calculate_player_fixture_projections(
    team: str,
    role: str,
    base_p_gioca: float,
    base_voto_mean: float,
    base_voto_std: float,
    base_bonus: float
) -> List[Dict]:
    """
    Funzione helper per calcolo proiezioni giocatore

    Wrapper per uso in player_service
    """
    calculator = get_fixture_calculator()

    return calculator.calculate_player_projections_per_matchday(
        team=team,
        role=role,
        base_p_gioca=base_p_gioca,
        base_voto_mean=base_voto_mean,
        base_voto_std=base_voto_std,
        base_bonus=base_bonus
    )
