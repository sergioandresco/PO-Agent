"""Job hand-off.

In AWS, POST /jobs returns 202 and the work happens in a Lambda triggered by
SQS (§12: never process synchronously inside a request). Locally there is no
queue, so `enqueue_job` reports that it did nothing and the caller falls back to
a FastAPI background task — same contract, one process.
"""

import json
import os


def queue_url() -> str | None:
    return os.environ.get("SQS_QUEUE_URL") or None


def enqueue_job(job_id: str, user_id: str, meeting_id: str) -> bool:
    """Returns True when the job was handed to SQS, False when no queue exists.

    The message carries only identifiers; the transcript stays in S3. Keeping the
    payload small is what stops a long meeting from blowing SQS's 256 KB limit.
    """
    url = queue_url()
    if url is None:
        return False

    import boto3

    client = boto3.client("sqs")
    client.send_message(
        QueueUrl=url,
        MessageBody=json.dumps({"jobId": job_id, "userId": user_id, "meetingId": meeting_id}),
    )
    return True
