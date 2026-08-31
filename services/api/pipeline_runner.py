import logging

from services.pipeline.llm import get_provider
from services.pipeline.orchestrator import run_pipeline

from . import job_store

logger = logging.getLogger("po_agent.runner")


async def execute_job(job_id: str, user_id: str, meeting_id: str, transcript: str) -> None:
    """Runs the pipeline after POST /jobs has already returned 202 (§12: never
    process synchronously inside a request). Locally this is an asyncio background
    task; in AWS the same function runs inside the SQS-triggered worker Lambda.
    In phase 2 its body becomes the Step Functions state machine."""
    job_store.mark_running(job_id, user_id)
    provider = get_provider()
    try:
        backlog = await run_pipeline(
            job_id=job_id,
            meeting_id=meeting_id,
            raw_transcript=transcript,
            provider=provider,
            on_stage=lambda stage: job_store.set_stage(job_id, user_id, stage),
        )
        job_store.set_result(job_id, user_id, backlog)
        job_store.mark_completed(job_id, user_id)
    except Exception as exc:
        # El estado del job es para el usuario; el traceback es para quien depura.
        # Guardar solo el primero deja CloudWatch mudo justo cuando hace falta.
        logger.exception("job %s failed: %s", job_id, exc)
        job_store.mark_failed(job_id, user_id, str(exc))
