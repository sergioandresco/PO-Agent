from typing import Literal

from pydantic import BaseModel, Field

from services.pipeline.llm import LlmProvider
from services.pipeline.llm.structured import complete_structured
from services.pipeline.models import BacklogResult, Estimate, EstimateMethod, PipelineStage

_SYSTEM_PROMPT = (
    "Eres un Product Owner experimentado estimando historias de usuario con la "
    "escala de Fibonacci (1, 2, 3, 5, 8, 13 story points). Basa la estimacion en la "
    "complejidad implicita en la historia, sus criterios de aceptacion y sus "
    "subtareas. Justifica cada estimacion en una frase."
)


class _EstimateEntry(BaseModel):
    story_index: int
    story_points: Literal[1, 2, 3, 5, 8, 13]
    rationale: str
    confidence: float = Field(ge=0, le=1)


class _EstimationResult(BaseModel):
    estimates: list[_EstimateEntry] = Field(default_factory=list)


def _format_stories(backlog: BacklogResult) -> str:
    lines = []
    for index, story in enumerate(backlog.stories):
        criteria = "; ".join(
            f"dado {ac.given}, cuando {ac.when}, entonces {ac.then}"
            for ac in story.acceptance_criteria
        )
        lines.append(
            f"[{index}] Como {story.as_a}, quiero {story.i_want}, para {story.so_that}. "
            f"Criterios: {criteria}. Subtareas: {len(story.subtasks)}."
        )
    return "\n".join(lines)


async def estimate(job_id: str, backlog: BacklogResult, provider: LlmProvider) -> BacklogResult:
    if not backlog.stories:
        return backlog

    prompt = (
        "Estas son las historias de usuario a estimar, con su indice:\n\n"
        f"{_format_stories(backlog)}\n\n"
        "Da una estimacion para cada una."
    )
    result = await complete_structured(
        provider,
        job_id=job_id,
        stage=PipelineStage.ESTIMATE,
        system=_SYSTEM_PROMPT,
        prompt=prompt,
        response_model=_EstimationResult,
    )

    by_index = {
        entry.story_index: entry
        for entry in result.estimates
        if 0 <= entry.story_index < len(backlog.stories)
    }
    updated_stories = []
    for index, story in enumerate(backlog.stories):
        entry = by_index.get(index)
        if entry is None:
            updated_stories.append(story)
            continue
        updated_stories.append(
            story.model_copy(
                update={
                    "estimate": Estimate(
                        story_points=entry.story_points,
                        rationale=entry.rationale,
                        method=EstimateMethod.LLM_REASONING,
                        confidence=entry.confidence,
                    )
                }
            )
        )
    return backlog.model_copy(update={"stories": updated_stories})
