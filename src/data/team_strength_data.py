"""Shared helpers for versioned team-strength datasets."""
from __future__ import annotations

from statistics import median
from typing import Any, Dict, Iterable, Mapping


NEUTRAL_STRENGTH = 5.0


def unwrap_teams(data: Mapping[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    """Accept both legacy and versioned team-strength JSON payloads."""
    if not isinstance(data, Mapping):
        return {}
    teams = data.get("teams", data)
    if not isinstance(teams, Mapping):
        return {}
    return {
        str(team): dict(values)
        for team, values in teams.items()
        if isinstance(values, Mapping)
    }


def clamp_strength(value: Any, default: float = NEUTRAL_STRENGTH) -> float:
    try:
        return max(1.0, min(10.0, float(value)))
    except (TypeError, ValueError):
        return default


def role_strength(values: Mapping[str, Any], role: str | None = None) -> float:
    """
    Return the opponent matchup strength for a player role.

    The primary opposing department remains the main driver:
    - P/D: opponent attack
    - C: opponent defense
    - A: opponent defense

    Midfield is now used as a secondary context modifier because a strong
    midfield affects the control and quality of the match without replacing
    the directly opposing department.

    Weights:
    - P/D: 80% attack + 20% midfield
    - C:   70% defense + 30% midfield
    - A:   85% defense + 15% midfield

    Missing midfield/primary values fall back to the team's overall strength.
    """
    normalized_role = str(role or "").strip().upper()[:1]

    overall = clamp_strength(values.get("overall"))
    midfield = clamp_strength(values.get("midfield"), default=overall)

    if normalized_role in {"P", "D"}:
        attack = clamp_strength(values.get("attack"), default=overall)
        return clamp_strength(attack * 0.80 + midfield * 0.20)

    if normalized_role == "C":
        defense = clamp_strength(values.get("defense"), default=overall)
        return clamp_strength(defense * 0.70 + midfield * 0.30)

    if normalized_role == "A":
        defense = clamp_strength(values.get("defense"), default=overall)
        return clamp_strength(defense * 0.85 + midfield * 0.15)

    return overall


def rank_strength(position: Any, participants: Any) -> float | None:
    """Normalize a table position to the shared 1-10 strength scale."""
    try:
        position = int(position)
        participants = int(participants)
    except (TypeError, ValueError):
        return None
    if participants < 2 or position < 1 or position > participants:
        return None
    return 1.0 + 9.0 * (participants - position) / (participants - 1)


def standings_from_mapping(raw_standings: Mapping[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    """Normalize legacy standings constants into a data-only representation."""
    if not isinstance(raw_standings, Mapping):
        return {}
    participants = len(raw_standings)
    standings: Dict[str, Dict[str, Any]] = {}
    for team, values in raw_standings.items():
        if not isinstance(values, Mapping):
            continue
        position = values.get("pos", values.get("posizione"))
        standings[str(team)] = {
            "position": position,
            "points": values.get("pts", values.get("punti")),
            "gf": values.get("gf", values.get("gol_fatti")),
            "gs": values.get("gs", values.get("gol_subiti")),
            "participants": participants,
        }
    return standings


def median_strength(teams: Iterable[Mapping[str, Any]], field: str) -> float:
    values = [clamp_strength(team.get(field)) for team in teams if field in team]
    return median(values) if values else NEUTRAL_STRENGTH
