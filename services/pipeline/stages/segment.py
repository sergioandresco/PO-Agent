from pydantic import BaseModel, Field

from services.pipeline.llm import LlmProvider
from services.pipeline.llm.structured import complete_structured
from services.pipeline.models import PipelineStage

from .formatting import format_utterances_for_prompt
from .types import Segment, Utterance

_SYSTEM_PROMPT = (
    "Eres un analista de producto que organiza transcripciones de reuniones en "
    "espanol en segmentos tematicos. Agrupa las utterances (identificadas por su "
    "indice) en segmentos coherentes por tema, respetando el orden en que aparecen. "
    "Cada utterance debe pertenecer a exactamente un segmento, y ningun indice puede "
    "quedar fuera."
)


class _SegmentBoundary(BaseModel):
    id: str
    title: str
    utterance_indices: list[int] = Field(min_length=1)


class _SegmentationResult(BaseModel):
    segments: list[_SegmentBoundary] = Field(min_length=1)


async def segment(job_id: str, utterances: list[Utterance], provider: LlmProvider) -> list[Segment]:
    prompt = (
        "Estas son las utterances de una reunion, con su indice:\n\n"
        f"{format_utterances_for_prompt(utterances)}\n\n"
        "Agrupalas en segmentos tematicos. Cada segmento necesita: un id corto en "
        "snake_case (ej. 'notificaciones_push'), un titulo descriptivo, y la lista "
        "de indices de utterances que le pertenecen."
    )
    result = await complete_structured(
        provider,
        job_id=job_id,
        stage=PipelineStage.SEGMENT,
        system=_SYSTEM_PROMPT,
        prompt=prompt,
        response_model=_SegmentationResult,
    )

    by_index = {u.index: u for u in utterances}
    segments: list[Segment] = []
    for boundary in result.segments:
        segment_utterances = [by_index[i] for i in boundary.utterance_indices if i in by_index]
        if not segment_utterances:
            continue
        segments.append(
            Segment(id=boundary.id, title=boundary.title, utterances=segment_utterances)
        )
    return segments
