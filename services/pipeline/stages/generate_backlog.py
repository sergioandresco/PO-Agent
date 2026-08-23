from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from services.pipeline.llm import LlmProvider
from services.pipeline.llm.structured import complete_structured
from services.pipeline.models import (
    AcceptanceCriterion,
    ArtifactStatus,
    BacklogResult,
    Epic,
    Feature,
    PipelineStage,
    Refinement,
    SourceReference,
    Subtask,
    UserStory,
)

from .types import EpicGroup, Segment, StoryCandidate, StoryRefinementEntry, Utterance

_SYSTEM_PROMPT = (
    "Eres un Product Owner organizando un backlog en espanol. Recibes historias de "
    "usuario ya redactadas (identificadas por indice) y debes agruparlas en features, "
    "y las features en epicas, segun similitud tematica. Tambien debes escribir el "
    "refinamiento de cada historia: supuestos, dependencias, riesgos, preguntas "
    "abiertas y criterios de 'definition of done'. No inventes historias nuevas: usa "
    "solo los indices que te doy."
)

PIPELINE_VERSION = "0.1.0"


class _BacklogOrganization(BaseModel):
    epics: list[EpicGroup] = Field(min_length=1)
    story_refinements: list[StoryRefinementEntry] = Field(default_factory=list)


def _format_story_candidates(candidates: list[StoryCandidate]) -> str:
    lines = []
    for index, candidate in enumerate(candidates):
        lines.append(
            f"[{index}] {candidate.title} — Como {candidate.as_a}, quiero "
            f"{candidate.i_want}, para {candidate.so_that}."
        )
    return "\n".join(lines)


def _build_sources(
    indices: list[int],
    utterances_by_index: dict[int, Utterance],
    segment_by_utterance_index: dict[int, str],
) -> list[SourceReference]:
    seen: dict[tuple[int, int], SourceReference] = {}
    for index in indices:
        utterance = utterances_by_index.get(index)
        if utterance is None:
            continue
        key = (utterance.start_char_offset, utterance.end_char_offset)
        if key in seen:
            continue
        seen[key] = SourceReference(
            segment_id=segment_by_utterance_index.get(index, "unknown"),
            start_char_offset=utterance.start_char_offset,
            end_char_offset=utterance.end_char_offset,
            start_time_ms=utterance.timestamp_ms,
            speaker=utterance.speaker,
            verbatim=utterance.text,
        )
    return list(seen.values())


async def generate_backlog(
    job_id: str,
    meeting_id: str,
    story_candidates: list[StoryCandidate],
    utterances: list[Utterance],
    segments: list[Segment],
    provider: LlmProvider,
) -> BacklogResult:
    if not story_candidates:
        return BacklogResult(
            meeting_id=meeting_id,
            epics=[],
            features=[],
            stories=[],
            generated_at=datetime.now(UTC),
            pipeline_version=PIPELINE_VERSION,
        )

    prompt = (
        "Estas son las historias de usuario candidatas, con su indice:\n\n"
        f"{_format_story_candidates(story_candidates)}\n\n"
        "Agrupalas en epicas y features. Cada epica y cada feature necesita titulo y "
        "descripcion. Cada feature debe listar los indices de las historias que le "
        "pertenecen (toda historia debe quedar en exactamente una feature). Ademas, "
        "para cada indice de historia, escribe su refinamiento."
    )
    organization = await complete_structured(
        provider,
        job_id=job_id,
        stage=PipelineStage.GENERATE_BACKLOG,
        system=_SYSTEM_PROMPT,
        prompt=prompt,
        response_model=_BacklogOrganization,
    )

    utterances_by_index = {u.index: u for u in utterances}
    segment_by_utterance_index = {
        u.index: seg.id for seg in segments for u in seg.utterances
    }
    refinement_by_story_index = {
        entry.story_index: Refinement(**entry.refinement.model_dump())
        for entry in organization.story_refinements
    }

    epics: list[Epic] = []
    features: list[Feature] = []
    stories: list[UserStory] = []

    for epic_group in organization.epics:
        epic_id = f"epic_{uuid4().hex[:8]}"
        epic_story_indices: list[int] = []

        for feature_group in epic_group.features:
            feature_id = f"feature_{uuid4().hex[:8]}"
            feature_story_indices: list[int] = []

            for story_index in feature_group.story_indices:
                if not 0 <= story_index < len(story_candidates):
                    continue
                candidate = story_candidates[story_index]
                sources = _build_sources(
                    candidate.supporting_utterance_indices,
                    utterances_by_index,
                    segment_by_utterance_index,
                )
                if not sources:
                    continue

                stories.append(
                    UserStory(
                        id=f"story_{uuid4().hex[:8]}",
                        feature_id=feature_id,
                        as_a=candidate.as_a,
                        i_want=candidate.i_want,
                        so_that=candidate.so_that,
                        acceptance_criteria=[
                            AcceptanceCriterion(
                                id=f"ac_{uuid4().hex[:6]}",
                                given=ac.given,
                                when=ac.when,
                                then=ac.then,
                            )
                            for ac in candidate.acceptance_criteria
                        ],
                        subtasks=[
                            Subtask(
                                id=f"subtask_{uuid4().hex[:6]}",
                                title=st.title,
                                description=st.description,
                                discipline=st.discipline,
                                estimated_hours=st.estimated_hours,
                            )
                            for st in candidate.subtasks
                        ],
                        refinement=refinement_by_story_index.get(story_index, Refinement()),
                        estimate=None,
                        confidence=candidate.confidence,
                        status=ArtifactStatus.DRAFT,
                        sources=sources,
                    )
                )
                feature_story_indices.append(story_index)

            if not feature_story_indices:
                continue
            feature_sources = _build_sources(
                [
                    i
                    for idx in feature_story_indices
                    for i in story_candidates[idx].supporting_utterance_indices
                ],
                utterances_by_index,
                segment_by_utterance_index,
            )
            if not feature_sources:
                continue
            features.append(
                Feature(
                    id=feature_id,
                    epic_id=epic_id,
                    title=feature_group.title,
                    description=feature_group.description,
                    status=ArtifactStatus.DRAFT,
                    sources=feature_sources,
                )
            )
            epic_story_indices.extend(feature_story_indices)

        if not epic_story_indices:
            continue
        epic_sources = _build_sources(
            [
                i
                for idx in epic_story_indices
                for i in story_candidates[idx].supporting_utterance_indices
            ],
            utterances_by_index,
            segment_by_utterance_index,
        )
        if not epic_sources:
            continue
        epics.append(
            Epic(
                id=epic_id,
                title=epic_group.title,
                description=epic_group.description,
                status=ArtifactStatus.DRAFT,
                sources=epic_sources,
            )
        )

    return BacklogResult(
        meeting_id=meeting_id,
        epics=epics,
        features=features,
        stories=stories,
        generated_at=datetime.now(UTC),
        pipeline_version=PIPELINE_VERSION,
    )
