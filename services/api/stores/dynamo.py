"""DynamoDB + S3 store — the production backend.

Single table, keys exactly as CLAUDE.md §6 specifies:

    Job          PK = USER#{userId}      SK = JOB#{jobId}
    Resultado    PK = JOB#{jobId}        SK = RESULT#v1
    Artefacto    PK = JOB#{jobId}        SK = ARTIFACT#{type}#{id}

plus one index item per artifact, PK = ARTIFACT#{id} / SK = INDEX, which is what
lets `PATCH /artifacts/{id}` resolve an artifact back to its job without
scanning. GSI1 (STATUS#{status}) lists in-flight jobs across users.

Two deliberate choices worth knowing about:

* **Artifacts are separate items, not one big result blob.** A finished backlog
  can exceed DynamoDB's 400 KB item limit, and patching one story would
  otherwise mean rewriting the whole result. `get_result` reassembles the
  BacklogResult from a single Query.

* **Model state is stored as a JSON string in `body`.** DynamoDB has no float
  type, and these models are full of them (`confidence`, `estimatedHours`).
  Round-tripping through Decimal is lossy and noisy; JSON is neither, and we
  never query inside these attributes.

Raw transcripts go to S3, never DynamoDB: they are the one unbounded input.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from services.pipeline.models import (
    BacklogResult,
    Epic,
    Feature,
    Job,
    JobStatus,
    PipelineStage,
    UserStory,
)

from .base import Artifact, ArtifactType

if TYPE_CHECKING:  # pragma: no cover - typing only
    from mypy_boto3_dynamodb.service_resource import Table
    from mypy_boto3_s3.client import S3Client

_MODEL_BY_TYPE: dict[ArtifactType, type[Epic] | type[Feature] | type[UserStory]] = {
    "epic": Epic,
    "feature": Feature,
    "story": UserStory,
}

RESULT_SK = "RESULT#v1"


def _user_pk(user_id: str) -> str:
    return f"USER#{user_id}"


def _job_sk(job_id: str) -> str:
    return f"JOB#{job_id}"


def _job_pk(job_id: str) -> str:
    return f"JOB#{job_id}"


def _artifact_sk(artifact_type: ArtifactType, artifact_id: str) -> str:
    return f"ARTIFACT#{artifact_type}#{artifact_id}"


def _artifact_index_pk(artifact_id: str) -> str:
    return f"ARTIFACT#{artifact_id}"


class DynamoJobStore:
    def __init__(
        self,
        table_name: str,
        bucket: str,
        *,
        table: Table | None = None,
        s3: S3Client | None = None,
    ) -> None:
        self._bucket = bucket
        if table is None or s3 is None:
            import boto3

            table = table or boto3.resource("dynamodb").Table(table_name)
            s3 = s3 or boto3.client("s3")
        self._table = table
        self._s3 = s3

    # ----- transcripts (S3) ------------------------------------------------

    def _transcript_key(self, job_id: str) -> str:
        return f"transcripts/{job_id}.txt"

    def get_transcript(self, job_id: str) -> str | None:
        try:
            obj = self._s3.get_object(Bucket=self._bucket, Key=self._transcript_key(job_id))
        except self._s3.exceptions.NoSuchKey:
            # A job with no transcript is a real, reportable state; any other S3
            # failure is a fault and must not be disguised as "not found".
            return None
        return obj["Body"].read().decode("utf-8")

    # ----- jobs ------------------------------------------------------------

    def create_job(self, user_id: str, meeting_id: str, transcript: str) -> Job:
        job_id = f"job_{uuid4().hex[:8]}"
        job = Job(
            job_id=job_id,
            user_id=user_id,
            meeting_id=meeting_id,
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
        )
        self._s3.put_object(
            Bucket=self._bucket,
            Key=self._transcript_key(job_id),
            Body=transcript.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
        )
        self._put_job(job)
        return job

    def _put_job(self, job: Job) -> None:
        self._table.put_item(
            Item={
                "pk": _user_pk(job.user_id),
                "sk": _job_sk(job.job_id),
                "entity": "job",
                "jobId": job.job_id,
                "userId": job.user_id,
                "createdAt": job.created_at.isoformat(),
                "gsi1pk": f"STATUS#{job.status.value}",
                "gsi1sk": _job_sk(job.job_id),
                "body": job.model_dump_json(by_alias=True),
            }
        )

    def list_jobs(self, user_id: str) -> list[Job]:
        from boto3.dynamodb.conditions import Key

        response = self._table.query(
            KeyConditionExpression=Key("pk").eq(_user_pk(user_id)) & Key("sk").begins_with("JOB#")
        )
        jobs = [Job.model_validate_json(str(item["body"])) for item in response.get("Items", [])]
        return sorted(jobs, key=lambda job: job.created_at, reverse=True)

    def get_job(self, job_id: str, user_id: str) -> Job | None:
        response = self._table.get_item(Key={"pk": _user_pk(user_id), "sk": _job_sk(job_id)})
        item = response.get("Item")
        if item is None:
            return None
        return Job.model_validate_json(str(item["body"]))

    def _patch_job(self, job_id: str, user_id: str, **updates: Any) -> None:
        job = self.get_job(job_id, user_id)
        if job is None:
            return
        self._put_job(job.model_copy(update=updates))

    def mark_running(self, job_id: str, user_id: str) -> None:
        self._patch_job(job_id, user_id, status=JobStatus.RUNNING)

    def set_stage(self, job_id: str, user_id: str, stage: PipelineStage) -> None:
        self._patch_job(job_id, user_id, current_stage=stage)

    def mark_completed(self, job_id: str, user_id: str) -> None:
        self._patch_job(
            job_id,
            user_id,
            status=JobStatus.COMPLETED,
            current_stage=None,
            completed_at=datetime.now(UTC),
        )

    def mark_failed(self, job_id: str, user_id: str, error: str) -> None:
        self._patch_job(
            job_id,
            user_id,
            status=JobStatus.FAILED,
            error=error,
            completed_at=datetime.now(UTC),
        )

    # ----- results and artifacts ------------------------------------------

    def set_result(self, job_id: str, user_id: str, result: BacklogResult) -> None:
        if self.get_job(job_id, user_id) is None:
            return

        with self._table.batch_writer() as batch:
            batch.put_item(
                Item={
                    "pk": _job_pk(job_id),
                    "sk": RESULT_SK,
                    "entity": "result",
                    "meetingId": result.meeting_id,
                    "generatedAt": result.generated_at.isoformat(),
                    "pipelineVersion": result.pipeline_version,
                }
            )
            groups: list[tuple[ArtifactType, list[Artifact]]] = [
                ("epic", list(result.epics)),
                ("feature", list(result.features)),
                ("story", list(result.stories)),
            ]
            for artifact_type, artifacts in groups:
                for artifact in artifacts:
                    batch.put_item(
                        Item={
                            "pk": _job_pk(job_id),
                            "sk": _artifact_sk(artifact_type, artifact.id),
                            "entity": "artifact",
                            "artifactType": artifact_type,
                            "body": artifact.model_dump_json(by_alias=True),
                        }
                    )
                    batch.put_item(
                        Item={
                            "pk": _artifact_index_pk(artifact.id),
                            "sk": "INDEX",
                            "entity": "artifact_index",
                            "jobId": job_id,
                            "artifactType": artifact_type,
                        }
                    )

    def get_result(self, job_id: str, user_id: str) -> BacklogResult | None:
        from boto3.dynamodb.conditions import Key

        if self.get_job(job_id, user_id) is None:
            return None

        response = self._table.query(KeyConditionExpression=Key("pk").eq(_job_pk(job_id)))
        items = response.get("Items", [])
        meta = next((item for item in items if item.get("sk") == RESULT_SK), None)
        if meta is None:
            return None

        epics: list[Epic] = []
        features: list[Feature] = []
        stories: list[UserStory] = []
        for item in items:
            if item.get("entity") != "artifact":
                continue
            body = str(item["body"])
            artifact_type = str(item["artifactType"])
            if artifact_type == "epic":
                epics.append(Epic.model_validate_json(body))
            elif artifact_type == "feature":
                features.append(Feature.model_validate_json(body))
            else:
                stories.append(UserStory.model_validate_json(body))

        return BacklogResult(
            meeting_id=str(meta["meetingId"]),
            epics=sorted(epics, key=lambda a: a.id),
            features=sorted(features, key=lambda a: a.id),
            stories=sorted(stories, key=lambda a: a.id),
            generated_at=datetime.fromisoformat(str(meta["generatedAt"])),
            pipeline_version=str(meta["pipelineVersion"]),
        )

    def get_artifact(
        self, artifact_id: str, user_id: str
    ) -> tuple[str, ArtifactType, Artifact] | None:
        index = self._table.get_item(
            Key={"pk": _artifact_index_pk(artifact_id), "sk": "INDEX"}
        ).get("Item")
        if index is None:
            return None

        job_id = str(index["jobId"])
        artifact_type = cast(ArtifactType, str(index["artifactType"]))

        # Ownership is re-checked here, not inherited from the index (§8).
        if self.get_job(job_id, user_id) is None:
            return None

        item = self._table.get_item(
            Key={"pk": _job_pk(job_id), "sk": _artifact_sk(artifact_type, artifact_id)}
        ).get("Item")
        if item is None:
            return None

        model_cls = _MODEL_BY_TYPE[artifact_type]
        artifact: Artifact = model_cls.model_validate_json(str(item["body"]))
        return job_id, artifact_type, artifact

    def update_artifact(
        self, job_id: str, user_id: str, artifact_type: ArtifactType, updated: Artifact
    ) -> None:
        if self.get_job(job_id, user_id) is None:
            return
        self._table.put_item(
            Item={
                "pk": _job_pk(job_id),
                "sk": _artifact_sk(artifact_type, updated.id),
                "entity": "artifact",
                "artifactType": artifact_type,
                "body": updated.model_dump_json(by_alias=True),
            }
        )

    def reset(self) -> None:
        raise RuntimeError("reset() is not available against DynamoDB")


def from_environment() -> DynamoJobStore | None:
    """Returns a DynamoDB store when the environment names a table, else None."""
    table_name = os.environ.get("DDB_TABLE_NAME")
    bucket = os.environ.get("S3_BUCKET_TRANSCRIPTS")
    if not table_name or not bucket:
        return None
    return DynamoJobStore(table_name=table_name, bucket=bucket)
