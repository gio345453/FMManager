from typing import Any

from web.backend.ai.gemini_client import run_tool_chat
from web.backend.ai.prompts import SYSTEM_PROMPT
from web.backend.ai.tools import TOOLS, build_tool_handlers
from web.backend.services.player_service import PlayerService


def chat(message: str, player_service: PlayerService) -> dict[str, Any]:
    """Run FantaAI using the PlayerService instance already owned by FastAPI."""
    prompt = f"{SYSTEM_PROMPT}\n\nMessaggio dell'utente:\n{message}"

    result = run_tool_chat(
        message=prompt,
        tools=TOOLS,
        tool_handlers=build_tool_handlers(player_service),
    )

    return result
