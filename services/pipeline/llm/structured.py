from pydantic import BaseModel, ValidationError

from services.pipeline.logging_utils import log_event
from services.pipeline.models import PipelineStage

from .provider import CompletionRequest, LlmProvider, LlmProviderError


async def complete_structured[T: BaseModel](
    provider: LlmProvider,
    *,
    job_id: str,
    stage: PipelineStage,
    system: str,
    prompt: str,
    response_model: type[T],
    max_output_tokens: int | None = None,
) -> T:
    """Calls the provider asking for JSON matching response_model's schema, validates
    it, and retries once with the validation error appended to the prompt (§7). Every
    call is logged with the exact model id, tokens, and latency for the report (§1, §7).
    """
    schema = response_model.model_json_schema()

    async def _call(text: str) -> T:
        request = CompletionRequest(
            prompt=text,
            system=system,
            response_schema=schema,
            max_output_tokens=max_output_tokens,
        )
        response = await provider.complete(request)
        log_event(
            job_id,
            stage,
            event="llm_call",
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            latency_ms=round(response.latency_ms, 1),
        )
        return response_model.model_validate_json(response.text)

    try:
        return await _call(prompt)
    except ValidationError as first_error:
        log_event(job_id, stage, event="validation_retry", error=str(first_error))
        retry_prompt = (
            f"{prompt}\n\n"
            "Tu respuesta anterior no fue un JSON válido contra el esquema requerido. "
            f"Error de validación:\n{first_error}\n\n"
            "Corrige la respuesta y devuelve únicamente el JSON válido, nada más."
        )
        try:
            return await _call(retry_prompt)
        except ValidationError as second_error:
            log_event(job_id, stage, event="validation_failed", error=str(second_error))
            raise LlmProviderError(
                f"LLM output failed schema validation twice for {response_model.__name__}: "
                f"{second_error}"
            ) from second_error
