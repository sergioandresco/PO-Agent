from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel


class CompletionRequest(BaseModel):
    prompt: str
    system: str | None = None
    response_schema: dict[str, Any] | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None


class CompletionResponse(BaseModel):
    """Every field here is required because §7 of CLAUDE.md mandates logging
    the exact model id, tokens in/out, and latency for every LLM call."""

    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    created_at: datetime


class LlmProviderError(RuntimeError):
    """Raised when the underlying provider API call fails."""


class LlmProvider(Protocol):
    name: str

    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
