from collections.abc import Callable
from datetime import UTC, datetime

from services.pipeline.llm import LlmProvider
from services.pipeline.logging_utils import log_event
from services.pipeline.models import BacklogResult, PipelineStage
from services.pipeline.stages import (
    classify,
    estimate,
    extract_entities,
    generate_backlog,
    normalize,
    segment,
    validate,
)
from services.pipeline.stages.types import StoryCandidate

OnStage = Callable[[PipelineStage], None] | None


async def run_pipeline(
    *,
    job_id: str,
    meeting_id: str,
    raw_transcript: str,
    provider: LlmProvider,
    on_stage: OnStage = None,
) -> BacklogResult:
    """Runs every stage in sequence against a raw transcript. Shared by the local
    script (run_local.py) and the API's background job runner so both drive the
    exact same pipeline code (§10: no business logic duplicated across entry points)."""

    def notify(stage: PipelineStage) -> None:
        if on_stage is not None:
            on_stage(stage)

    started = datetime.now(UTC)

    notify(PipelineStage.NORMALIZE)
    utterances = normalize(raw_transcript)
    log_event(job_id, PipelineStage.NORMALIZE, utterance_count=len(utterances))
    if not utterances:
        raise ValueError(
            "normalize found no utterances in the transcript — check the format "
            "(expected 'Speaker: text' or '[HH:MM:SS] Speaker: text' lines)"
        )

    notify(PipelineStage.SEGMENT)
    segments = await segment(job_id, utterances, provider)
    log_event(job_id, PipelineStage.SEGMENT, segment_count=len(segments))

    all_story_candidates: list[StoryCandidate] = []
    for seg in segments:
        notify(PipelineStage.CLASSIFY)
        labels = await classify(job_id, seg, provider)
        log_event(job_id, PipelineStage.CLASSIFY, segment_id=seg.id, label_count=len(labels))

        notify(PipelineStage.EXTRACT_ENTITIES)
        candidates = await extract_entities(job_id, seg, labels, provider)
        log_event(
            job_id,
            PipelineStage.EXTRACT_ENTITIES,
            segment_id=seg.id,
            candidate_count=len(candidates),
        )
        all_story_candidates.extend(candidates)

    notify(PipelineStage.GENERATE_BACKLOG)
    backlog = await generate_backlog(
        job_id=job_id,
        meeting_id=meeting_id,
        story_candidates=all_story_candidates,
        utterances=utterances,
        segments=segments,
        provider=provider,
    )
    log_event(job_id, PipelineStage.GENERATE_BACKLOG, story_count=len(backlog.stories))

    notify(PipelineStage.ESTIMATE)
    backlog = await estimate(job_id, backlog, provider)
    log_event(
        job_id,
        PipelineStage.ESTIMATE,
        estimated_count=sum(1 for s in backlog.stories if s.estimate is not None),
    )

    notify(PipelineStage.VALIDATE)
    backlog = validate(backlog)
    log_event(job_id, PipelineStage.VALIDATE, final_story_count=len(backlog.stories))

    elapsed = (datetime.now(UTC) - started).total_seconds()
    log_event(job_id, "pipeline", total_seconds=round(elapsed, 2))

    return backlog
