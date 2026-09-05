import json
import os
from typing import Any, Callable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY non configurata")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(timeout=60000),
)

MODEL = "gemini-3.6-flash"


def ask_gemini(message: str) -> str:
    """Simple text request used for connectivity/basic chat tests."""
    interaction = client.interactions.create(
        model=MODEL,
        input=message,
    )

    if not interaction.output_text:
        raise RuntimeError("Gemini ha restituito una risposta vuota")

    return interaction.output_text


def run_tool_chat(
    message: str,
    tools: list[dict[str, Any]],
    tool_handlers: dict[str, Callable[..., Any]],
) -> dict[str, Any]:
    """
    Run a stateless Gemini interaction loop and execute application tools.

    Returns both the final response and the exact tool names used across
    all tool-calling steps.
    """
    history: list[dict[str, Any]] = [
        {
            "type": "user_input",
            "content": [{"type": "text", "text": message}],
        }
    ]

    tools_used: list[str] = []

    for _ in range(4):
        interaction = client.interactions.create(
            model=MODEL,
            store=False,
            input=history,
            tools=tools,
        )

        function_calls = [
            step for step in interaction.steps
            if step.type == "function_call"
        ]

        if not function_calls:
            return {
                "response": interaction.output_text or "",
                "tools_used": tools_used,
            }

        # Keep Gemini's emitted steps in the next request.
        for step in interaction.steps:
            history.append(step.model_dump())

        for call in function_calls:
            tool_name = call.name
            arguments = call.arguments or {}
            handler = tool_handlers.get(tool_name)

            print(f"[FantaAI] Tool call: {tool_name}({arguments})", flush=True)

            if handler is None:
                result: Any = {
                    "error": f"Strumento non disponibile: {tool_name}"
                }
            else:
                try:
                    result = handler(**arguments)
                except Exception as exc:
                    result = {"error": str(exc)}

            tools_used.append(tool_name)

            print(f"[FantaAI] Tool result: {result}", flush=True)

            history.append(
                {
                    "type": "function_result",
                    "name": tool_name,
                    "call_id": call.id,
                    "result": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False),
                        }
                    ],
                }
            )

    raise RuntimeError("Numero massimo di chiamate tool superato")
