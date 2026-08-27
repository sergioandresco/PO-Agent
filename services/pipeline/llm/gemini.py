import time
from datetime import UTC, datetime
from typing import Any

from google import genai
from google.genai import errors as genai_errors

from .provider import CompletionRequest, CompletionResponse, LlmProviderError


class GeminiProvider:
    """Talks to Gemini's Interactions API (google-genai SDK).

    Note: unlike the classic generate_content API, the Interactions API's
    GenerationConfig has no `temperature` field, so CompletionRequest.temperature
    is accepted for interface compatibility with other providers but ignored here.
    """

    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        response_format: dict[str, Any] | None = None
        if request.response_schema is not None:
            response_format = {
                "type": "text",
                "mime_type": "application/json",
                "schema": request.response_schema,
            }

        generation_config: dict[str, Any] = {}
        if request.max_output_tokens is not None:
            generation_config["max_output_tokens"] = request.max_output_tokens

        started = time.perf_counter()
        try:
            interaction = await self._client.aio.interactions.create(
                model=self._model,
                input=request.prompt,
                system_instruction=request.system,
                response_format=response_format,
                generation_config=generation_config or None,
            )
        except genai_errors.APIError as exc:
            raise LlmProviderError(f"Gemini API call failed: {exc}") from exc
        latency_ms = (time.perf_counter() - started) * 1000

        usage = interaction.usage  # type: ignore[union-attr]
        return CompletionResponse(
            text=interaction.output_text or "",  # type: ignore[union-attr]
            provider=self.name,
            model=interaction.model or self._model,  # type: ignore[union-attr]
            input_tokens=(usage.total_input_tokens or 0) if usage else 0,
            output_tokens=(usage.total_output_tokens or 0) if usage else 0,
            latency_ms=latency_ms,
            created_at=datetime.now(UTC),
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Embeddings are only needed for the RAG phase (CLAUDE.md §3.1.d)")
