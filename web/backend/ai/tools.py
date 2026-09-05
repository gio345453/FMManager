from typing import Any, Callable

from web.backend.services.comparison_service import ComparisonService
from web.backend.services.player_service import PlayerService


GET_PLAYER_TOOL = {
    "type": "function",
    "name": "get_player",
    "description": (
        "Recupera i dati completi di un giocatore presenti in FMManager. "
        "Usa questo strumento prima di rispondere a domande specifiche su un giocatore."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "player_id": {
                "type": "integer",
                "description": "ID numerico del giocatore presente in FMManager",
            },
            "budget": {
                "type": "number",
                "description": "Budget asta usato per calcolare il prezzo del giocatore",
            },
        },
        "required": ["player_id"],
    },
}

SEARCH_PLAYERS_TOOL = {
    "type": "function",
    "name": "search_players",
    "description": (
        "Cerca giocatori nei dati di FMManager. Può filtrare per nome, ruolo o "
        "squadra e restituire una lista ordinata. Usa questo strumento quando "
        "l'utente indica un giocatore per nome ma non conosci il suo ID."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Nome o parte del nome"},
            "role": {"type": "string", "description": "Ruolo P, D, C o A"},
            "team": {"type": "string", "description": "Squadra"},
            "limit": {
                "type": "integer",
                "description": "Numero massimo di risultati",
                "default": 10,
            },
            "budget": {
                "type": "number",
                "description": "Budget asta",
                "default": 500,
            },
        },
    },
}

COMPARE_PLAYERS_TOOL = {
    "type": "function",
    "name": "compare_players",
    "description": (
        "Confronta 2 o 3 giocatori usando esclusivamente i dati e i calcoli "
        "di ComparisonService di FMManager. Prima recupera gli ID dei giocatori "
        "con search_players quando sono indicati per nome."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "player_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 2,
                "maxItems": 3,
                "description": "ID di 2 o 3 giocatori da confrontare",
            },
            "budget": {
                "type": "number",
                "description": "Budget asta usato per il confronto dei prezzi",
                "default": 500,
            },
        },
        "required": ["player_ids"],
    },
}

TOOLS = [
    GET_PLAYER_TOOL,
    SEARCH_PLAYERS_TOOL,
    COMPARE_PLAYERS_TOOL,
]


def get_player(
    player_service: PlayerService,
    player_id: int,
    budget: float = 500,
) -> dict[str, Any]:
    player = player_service.get_player_by_id(player_id, budget)

    if player is None:
        return {"found": False, "player_id": player_id}

    return {"found": True, "player": player}


def search_players(
    player_service: PlayerService,
    search: str | None = None,
    role: str | None = None,
    team: str | None = None,
    limit: int = 10,
    budget: float = 500,
) -> list[dict[str, Any]]:
    players = player_service.get_all_players(
        search=search,
        role=role,
        team=team,
        budget=budget,
        sort_by="Overall",
        sort_order="desc",
    )

    return players[: max(1, min(limit, 50))]


def compare_players(
    player_service: PlayerService,
    player_ids: list[int],
    budget: float = 500,
) -> dict[str, Any]:
    if not 2 <= len(player_ids) <= 3:
        raise ValueError("Il confronto richiede 2 o 3 giocatori.")

    service = ComparisonService(player_service.df_with_overall)

    result = service.compare_players(
        player_ids=player_ids,
        budget=budget,
    )

    return result


def build_tool_handlers(player_service: PlayerService) -> dict[str, Callable[..., Any]]:
    """Create tool handlers bound to the already-loaded PlayerService instance."""
    return {
        "get_player": lambda **kwargs: get_player(player_service, **kwargs),
        "search_players": lambda **kwargs: search_players(player_service, **kwargs),
        "compare_players": lambda **kwargs: compare_players(player_service, **kwargs),
    }
