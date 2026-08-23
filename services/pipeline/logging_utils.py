import json
import logging

from services.pipeline.models import PipelineStage

logger = logging.getLogger("po_agent.pipeline")


def log_event(job_id: str, stage: PipelineStage | str, **fields: object) -> None:
    payload = {"jobId": job_id, "stage": str(stage), **fields}
    logger.info(json.dumps(payload, default=str, ensure_ascii=False))
