"""SQS-triggered pipeline worker.

POST /jobs returns 202 immediately and drops a message here; this Lambda picks it
up and runs the full pipeline (§12: never process synchronously inside a request).
The message carries only identifiers — the transcript is fetched from S3, which
keeps a long meeting from hitting SQS's 256 KB payload limit.

On failure `execute_job` records the error on the job and returns normally, so
SQS deletes the message rather than retrying. That is deliberate: every retry is
another round of paid LLM calls, and a job that failed on a bad transcript would
fail again identically. Malformed messages — the ones that never reach
`execute_job` — are reported as batch item failures and end up in the DLQ.

In phase 2 this handler is replaced by a Step Functions state machine with one
Lambda per pipeline stage, which is where per-stage retries become worthwhile.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from services.secrets import load_secrets_into_env

load_secrets_into_env()

from services.api import job_store  # noqa: E402
from services.api.pipeline_runner import execute_job  # noqa: E402

# `basicConfig` no hace nada en Lambda: el runtime ya instalo un handler en el root
# y lo dejo en WARNING, asi que todo lo que se emita con INFO se descarta en silencio.
# Subir el nivel del root explicitamente es lo que hace visibles las etapas del
# pipeline, que se registran con logger.info desde logging_utils.
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("po_agent.worker")


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    failures: list[dict[str, str]] = []

    for record in event.get("Records", []):
        message_id = str(record.get("messageId", ""))
        try:
            message = json.loads(record["body"])
            job_id = str(message["jobId"])
            user_id = str(message["userId"])
            meeting_id = str(message["meetingId"])
        except (KeyError, ValueError) as exc:
            logger.error(json.dumps({"event": "bad_message", "error": str(exc)}))
            failures.append({"itemIdentifier": message_id})
            continue

        transcript = job_store.get_transcript(job_id)
        if transcript is None:
            logger.error(json.dumps({"event": "transcript_missing", "jobId": job_id}))
            job_store.mark_failed(job_id, user_id, "Transcript not found in S3")
            continue

        logger.info(json.dumps({"event": "job_start", "jobId": job_id}))
        asyncio.run(execute_job(job_id, user_id, meeting_id, transcript))
        logger.info(json.dumps({"event": "job_end", "jobId": job_id}))

    return {"batchItemFailures": failures}
