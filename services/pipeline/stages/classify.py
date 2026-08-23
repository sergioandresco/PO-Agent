from pydantic import BaseModel, Field

from services.pipeline.llm import LlmProvider
from services.pipeline.llm.structured import complete_structured
from services.pipeline.models import PipelineStage

from .formatting import format_utterances_for_prompt
from .types import ClassifiedUtterance, Segment

_SYSTEM_PROMPT = (
    "Eres un clasificador de enunciados de reuniones de producto (fase 1 del "
    "clasificador: via prompt, sin modelo propio todavia). Para cada utterance, "
    "asigna exactamente una etiqueta: 'requirement' (algo que el producto debe "
    "hacer), 'risk' (un riesgo o bloqueo), 'decision' (una decision tomada), "
    "'constraint' (una restriccion tecnica o de negocio), 'question' (una pregunta "
    "abierta sin resolver), u 'off_topic' (charla que no aporta al backlog)."
)


class _ClassificationResult(BaseModel):
    labels: list[ClassifiedUtterance] = Field(min_length=1)


async def classify(
    job_id: str, seg: Segment, provider: LlmProvider
) -> list[ClassifiedUtterance]:
    prompt = (
        f"Segmento: {seg.title}\n\n"
        f"{format_utterances_for_prompt(seg.utterances)}\n\n"
        "Clasifica cada una de estas utterances por su indice."
    )
    result = await complete_structured(
        provider,
        job_id=job_id,
        stage=PipelineStage.CLASSIFY,
        system=_SYSTEM_PROMPT,
        prompt=prompt,
        response_model=_ClassificationResult,
    )
    valid_indices = {u.index for u in seg.utterances}
    return [label for label in result.labels if label.utterance_index in valid_indices]
