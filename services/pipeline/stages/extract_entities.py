from pydantic import BaseModel, Field

from services.pipeline.llm import LlmProvider
from services.pipeline.llm.structured import complete_structured
from services.pipeline.models import PipelineStage

from .formatting import format_utterances_for_prompt
from .types import ClassifiedUtterance, Segment, StoryCandidate, UtteranceLabel

_SYSTEM_PROMPT = (
    "Eres un Product Owner que redacta historias de usuario en espanol a partir de "
    "una reunion. Solo puedes usar utterances marcadas como 'requirement', 'risk', "
    "'decision' o 'constraint' como respaldo. Cada historia debe listar los indices "
    "exactos de las utterances que la respaldan; nunca inventes contenido que no este "
    "en el texto. Si el segmento no da para ninguna historia de usuario, devuelve una "
    "lista vacia."
)


class _ExtractionResult(BaseModel):
    stories: list[StoryCandidate] = Field(default_factory=list)


async def extract_entities(
    job_id: str,
    seg: Segment,
    labels: list[ClassifiedUtterance],
    provider: LlmProvider,
) -> list[StoryCandidate]:
    off_topic = {
        label.utterance_index for label in labels if label.label is UtteranceLabel.OFF_TOPIC
    }
    relevant = [u for u in seg.utterances if u.index not in off_topic]
    if not relevant:
        return []

    prompt = (
        f"Segmento: {seg.title}\n\n"
        f"{format_utterances_for_prompt(relevant)}\n\n"
        "Identifica las historias de usuario que se puedan redactar a partir de estas "
        "utterances. Para cada una: titulo, 'como [rol]', 'quiero [accion]', 'para "
        "[beneficio]', al menos un criterio de aceptacion (dado/cuando/entonces), "
        "subtareas si aplica (frontend/backend/database/infrastructure/qa/design), "
        "una confianza de 0 a 1, y la lista de indices de utterances que la respaldan "
        "(obligatoria, no puede ir vacia)."
    )
    result = await complete_structured(
        provider,
        job_id=job_id,
        stage=PipelineStage.EXTRACT_ENTITIES,
        system=_SYSTEM_PROMPT,
        prompt=prompt,
        response_model=_ExtractionResult,
    )

    valid_indices = {u.index for u in relevant}
    grounded_stories = []
    for story in result.stories:
        supporting = [i for i in story.supporting_utterance_indices if i in valid_indices]
        if not supporting:
            continue
        grounded_stories.append(
            story.model_copy(update={"supporting_utterance_indices": supporting})
        )
    return grounded_stories
