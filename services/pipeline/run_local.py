"""Runs the full backlog-generation pipeline against a transcript file on disk,
end to end, with no AWS involved (CLAUDE.md §11 step 3 — the project's most
important milestone). Prints the resulting BacklogResult as JSON.

Usage:
    uv run python -m services.pipeline.run_local
    uv run python -m services.pipeline.run_local path/to/transcript.txt meeting_id
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from services.pipeline.llm import get_provider
from services.pipeline.logging_utils import log_event
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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_meeting.txt"

logging.basicConfig(level=logging.INFO, format="%(message)s")


async def run_pipeline(transcript_path: Path, meeting_id: str) -> str:
    job_id = f"local_{uuid4().hex[:8]}"
    provider = get_provider()
    raw_transcript = transcript_path.read_text(encoding="utf-8")

    started = datetime.now(UTC)

    utterances = normalize(raw_transcript)
    log_event(job_id, "normalize", utterance_count=len(utterances))

    segments = await segment(job_id, utterances, provider)
    log_event(job_id, "segment", segment_count=len(segments))

    all_story_candidates: list[StoryCandidate] = []
    for seg in segments:
        labels = await classify(job_id, seg, provider)
        log_event(job_id, "classify", segment_id=seg.id, label_count=len(labels))

        candidates = await extract_entities(job_id, seg, labels, provider)
        log_event(
            job_id, "extract_entities", segment_id=seg.id, candidate_count=len(candidates)
        )
        all_story_candidates.extend(candidates)

    backlog = await generate_backlog(
        job_id=job_id,
        meeting_id=meeting_id,
        story_candidates=all_story_candidates,
        utterances=utterances,
        segments=segments,
        provider=provider,
    )
    log_event(job_id, "generate_backlog", story_count=len(backlog.stories))

    backlog = await estimate(job_id, backlog, provider)
    log_event(
        job_id,
        "estimate",
        estimated_count=sum(1 for s in backlog.stories if s.estimate is not None),
    )

    backlog = validate(backlog)
    log_event(job_id, "validate", final_story_count=len(backlog.stories))

    elapsed = (datetime.now(UTC) - started).total_seconds()
    log_event(job_id, "pipeline", total_seconds=round(elapsed, 2))

    return backlog.model_dump_json(by_alias=True, indent=2)


def main() -> None:
    load_dotenv(REPO_ROOT / ".env.local")

    transcript_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    meeting_id = sys.argv[2] if len(sys.argv) > 2 else transcript_path.stem

    result_json = asyncio.run(run_pipeline(transcript_path, meeting_id))
    print(result_json)


if __name__ == "__main__":
    main()
