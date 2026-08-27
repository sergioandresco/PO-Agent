import pytest

from services.pipeline.orchestrator import run_pipeline


async def test_run_pipeline_rejects_a_transcript_with_no_recognizable_utterances() -> None:
    with pytest.raises(ValueError, match="no utterances"):
        await run_pipeline(
            job_id="job_test",
            meeting_id="meeting_test",
            raw_transcript="Este documento no tiene ningun formato de dialogo reconocible.",
            provider=None,  # type: ignore[arg-type]
        )
