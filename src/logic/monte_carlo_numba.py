"""
Funzioni ottimizzate con Numba per Monte Carlo Simulator
Velocizzano i loop numerici critici di 5-10x
"""
import numpy as np
from numba import jit

@jit(nopython=True)
def simulate_player_vote(mv: float, consistency: float) -> float:
    """
    Simula il voto di un giocatore usando distribuzione normale

    Args:
        mv: Media voto
        consistency: Deviazione standard

    Returns:
        Voto simulato
    """
    return np.random.normal(mv, consistency)

@jit(nopython=True)
def simulate_poisson_events(rate: float) -> int:
    """
    Simula eventi con distribuzione di Poisson (gol, assist, ammonizioni)

    Args:
        rate: Tasso medio eventi

    Returns:
        Numero eventi simulati
    """
    if rate <= 0:
        return 0
    return np.random.poisson(rate)

@jit(nopython=True)
def calculate_virtual_goals(score: float, threshold: int, points_per_goal: int) -> int:
    """
    Calcola gol virtuali da punteggio

    Args:
        score: Punteggio totale squadra
        threshold: Soglia primo gol virtuale
        points_per_goal: Punti per ogni gol virtuale successivo

    Returns:
        Numero gol virtuali
    """
    if score < threshold:
        return 0
    return 1 + int((score - threshold) / points_per_goal)

@jit(nopython=True)
def simulate_lineup_performance(
    mvs: np.ndarray,  # Shape: (11,) - media voti titolari
    consistencies: np.ndarray,  # Shape: (11,)
    goal_rates: np.ndarray,  # Shape: (11,)
    assist_rates: np.ndarray,  # Shape: (11,)
    yellow_rates: np.ndarray,  # Shape: (11,)
    red_rates: np.ndarray,  # Shape: (11,)
    goal_bonus: float,
    assist_bonus: float,
    yellow_malus: float,
    red_malus: float
) -> float:
    """
    Simula performance di una lineup (11 giocatori)
    Ritorna score totale

    OTTIMIZZATO: Loop numerico puro, compilato con Numba
    """
    total_score = 0.0

    for i in range(11):
        # Voto base
        vote = simulate_player_vote(mvs[i], consistencies[i])
        total_score += vote

        # Eventi
        n_goals = simulate_poisson_events(goal_rates[i])
        n_assists = simulate_poisson_events(assist_rates[i])
        n_yellows = simulate_poisson_events(yellow_rates[i])
        n_reds = simulate_poisson_events(red_rates[i])

        # Bonus/Malus
        total_score += n_goals * goal_bonus
        total_score += n_assists * assist_bonus
        total_score -= n_yellows * yellow_malus
        total_score -= n_reds * red_malus

    return total_score

@jit(nopython=True)
def simulate_season_fast(
    n_simulations: int,
    n_matchdays: int,
    n_teams: int,
    team_lineups_mvs: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    team_lineups_consistencies: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    team_lineups_goal_rates: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    team_lineups_assist_rates: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    team_lineups_yellow_rates: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    team_lineups_red_rates: np.ndarray,  # Shape: (n_teams, n_matchdays, 11)
    fixtures: np.ndarray,  # Shape: (n_matchdays, n_fixtures, 2) - [home_idx, away_idx]
    goal_bonus: float,
    assist_bonus: float,
    yellow_malus: float,
    red_malus: float,
    threshold: int,
    points_per_goal: int
) -> np.ndarray:
    """
    Simula un'intera stagione in batch ottimizzato

    Returns:
        Array (n_simulations, n_teams) con posizioni finali
    """
    results = np.zeros((n_simulations, n_teams), dtype=np.int32)

    for sim_idx in range(n_simulations):
        # Classifica stagione
        points = np.zeros(n_teams, dtype=np.int32)
        goals_for = np.zeros(n_teams, dtype=np.int32)
        goals_against = np.zeros(n_teams, dtype=np.int32)

        # Simula ogni matchday
        for md in range(n_matchdays):
            # Calcola score per ogni squadra
            scores = np.zeros(n_teams, dtype=np.float64)
            virtual_goals_arr = np.zeros(n_teams, dtype=np.int32)

            for team_idx in range(n_teams):
                score = simulate_lineup_performance(
                    team_lineups_mvs[team_idx, md, :],
                    team_lineups_consistencies[team_idx, md, :],
                    team_lineups_goal_rates[team_idx, md, :],
                    team_lineups_assist_rates[team_idx, md, :],
                    team_lineups_yellow_rates[team_idx, md, :],
                    team_lineups_red_rates[team_idx, md, :],
                    goal_bonus,
                    assist_bonus,
                    yellow_malus,
                    red_malus
                )
                scores[team_idx] = score
                virtual_goals_arr[team_idx] = calculate_virtual_goals(
                    score, threshold, points_per_goal
                )

            # Processa fixture
            n_fixtures = fixtures.shape[1]
            for fix_idx in range(n_fixtures):
                home_idx = fixtures[md, fix_idx, 0]
                away_idx = fixtures[md, fix_idx, 1]

                if home_idx < 0 or away_idx < 0:  # Skip invalid
                    continue

                home_goals = virtual_goals_arr[home_idx]
                away_goals = virtual_goals_arr[away_idx]

                goals_for[home_idx] += home_goals
                goals_against[home_idx] += away_goals
                goals_for[away_idx] += away_goals
                goals_against[away_idx] += home_goals

                # Punti
                if home_goals > away_goals:
                    points[home_idx] += 3
                elif away_goals > home_goals:
                    points[away_idx] += 3
                else:
                    points[home_idx] += 1
                    points[away_idx] += 1

        # Calcola posizioni finali
        goal_diff = goals_for - goals_against

        # Sort multi-criterio
        order = np.argsort(goals_for)[::-1]
        order = order[np.argsort(goal_diff[order])][::-1]
        order = order[np.argsort(points[order])][::-1]

        # Converti in posizioni
        positions = np.zeros(n_teams, dtype=np.int32)
        for pos, team_idx in enumerate(order):
            positions[team_idx] = pos + 1

        results[sim_idx, :] = positions

    return results
