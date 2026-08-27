"""Runs the full backlog-generation pipeline against a transcript file on disk,
end to end, with no AWS involved (CLAUDE.md §11 step 3 — the project's most
important milestone). Prints the resulting BacklogResult as JSON to stdout;
everything else (stage logs) goes to stderr, so `> output.json` gives you a
clean file.

Usage:
    uv run python -m services.pipeline.run_local
    uv run python -m services.pipeline.run_local path/to/transcript.txt meeting_id
"""

import asyncio
import logging
import sys
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

from services.pipeline.llm import get_provider
from services.pipeline.orchestrator import run_pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FIXTURE = Path(__file__).parent / "fixtures" / "sample_meeting.txt"

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)


def main() -> None:
    load_dotenv(REPO_ROOT / ".env.local")

    transcript_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    meeting_id = sys.argv[2] if len(sys.argv) > 2 else transcript_path.stem

    job_id = f"local_{uuid4().hex[:8]}"
    provider = get_provider()
    raw_transcript = transcript_path.read_text(encoding="utf-8")

    backlog = asyncio.run(
        run_pipeline(
            job_id=job_id,
            meeting_id=meeting_id,
            raw_transcript=raw_transcript,
            provider=provider,
        )
    )
    print(backlog.model_dump_json(by_alias=True, indent=2))


if __name__ == "__main__":
    main()
