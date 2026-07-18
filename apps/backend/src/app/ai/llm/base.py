"""LLMProvider contract — same swappability pattern as embeddings/vectors.
M3 needs complete(); M4 adds streaming."""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Completion:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMProvider(Protocol):
    async def complete(self, system: str, user: str) -> Completion: ...
