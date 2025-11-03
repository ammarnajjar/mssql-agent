"""Simple LLM wrapper for OpenAI Chat API used by the agent.

This module keeps calls isolated so tests can mock `openai.ChatCompletion.create`.
"""
from __future__ import annotations
import os
from typing import Dict, Any

try:
    import openai
except Exception:  # pragma: no cover - test will mock
    openai = None


class LLMError(RuntimeError):
    pass


def get_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY")


def call_llm(system: str, user: str, model: str = "gpt-3.5-turbo", max_tokens: int = 512) -> Dict[str, Any]:
    """Call the OpenAI chat API and return the first assistant message.

    Raises LLMError on missing API key or client.
    """
    key = get_api_key()
    if not key:
        raise LLMError("OPENAI_API_KEY not set in environment")
    if openai is None:
        raise LLMError("openai package not available")

    openai.api_key = key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.0,
    )
    # defensive parsing
    try:
        return resp
    except Exception as exc:  # pragma: no cover - wrapper
        raise LLMError("LLM call failed") from exc
