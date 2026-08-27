from services.pipeline.llm import get_provider
from services.pipeline.orchestrator import run_pipeline

from . import job_store


async def execute_job(job_id: str, meeting_id: str, transcript: str) -> None:
    """Runs the pipeline in the background after POST /jobs returns 202 (§12: never
    process synchronously inside a request). In production this body becomes the
    Step Functions state machine; here it's an asyncio background task."""
    job_store.mark_running(job_id)
    provider = get_provider()
    try:
        backlog = await run_pipeline(
            job_id=job_id,
            meeting_id=meeting_id,
            raw_transcript=transcript,
            provider=provider,
            on_stage=lambda stage: job_store.set_stage(job_id, stage),
        )
        job_store.set_result(job_id, backlog)
        job_store.mark_completed(job_id)
    except Exception as exc:
        job_store.mark_failed(job_id, str(exc))
