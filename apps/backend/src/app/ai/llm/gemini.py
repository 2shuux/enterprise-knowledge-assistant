"""Gemini chat via google-genai.

Temperature 0.2: RAG answers should be grounded and repeatable, not
creative. Higher temperatures increase the risk of the model drifting
away from the provided context.
"""
import asyncio

from google import genai
from google.genai import types

from app.ai.llm.base import Completion
from app.core.logging import get_logger

log = get_logger("llm.gemini")

_MAX_RETRIES = 3


class GeminiLLMProvider:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to apps/backend/.env "
                "(get a free key at https://aistudio.google.com)"
            )
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, system: str, user: str) -> Completion:
        delay = 2.0
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system, temperature=0.2
                    ),
                )
                usage = getattr(response, "usage_metadata", None)
                return Completion(
                    text=response.text or "",
                    prompt_tokens=getattr(usage, "prompt_token_count", None),
                    completion_tokens=getattr(usage, "candidates_token_count", None),
                )
            except Exception as exc:  # noqa: BLE001
                if attempt == _MAX_RETRIES:
                    raise
                log.warning("llm_retry", attempt=attempt, error=str(exc), sleep=delay)
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")
