"""Storage seam for jobs, results and artifacts.

Two implementations live behind this Protocol: an in-memory one for local
development and tests, and a DynamoDB + S3 one for AWS. Nothing above this
layer knows which is in use.

Every method that reads or mutates a job takes `user_id`. That is not
redundancy: it is how §8 isolation is enforced at the storage boundary rather
than trusted from the caller. In DynamoDB the job's partition key *is* the
user, so a wrong `user_id` cannot reach another user's row at all.
"""

from typing import Literal, Protocol

from services.pipeline.models import (
    BacklogResult,
    Epic,
    Feature,
    Job,
    PipelineStage,
    UserStory,
)

ArtifactType = Literal["epic", "feature", "story"]
Artifact = Epic | Feature | UserStory


class JobStore(Protocol):
    def create_job(self, user_id: str, meeting_id: str, transcript: str) -> Job: ...

    def list_jobs(self, user_id: str) -> list[Job]: ...

    def get_job(self, job_id: str, user_id: str) -> Job | None: ...

    def get_transcript(self, job_id: str) -> str | None: ...

    def get_result(self, job_id: str, user_id: str) -> BacklogResult | None: ...

    def set_result(self, job_id: str, user_id: str, result: BacklogResult) -> None: ...

    def get_artifact(
        self, artifact_id: str, user_id: str
    ) -> tuple[str, ArtifactType, Artifact] | None: ...

    def update_artifact(
        self, job_id: str, user_id: str, artifact_type: ArtifactType, updated: Artifact
    ) -> None: ...

    def mark_running(self, job_id: str, user_id: str) -> None: ...

    def set_stage(self, job_id: str, user_id: str, stage: PipelineStage) -> None: ...

    def mark_completed(self, job_id: str, user_id: str) -> None: ...

    def mark_failed(self, job_id: str, user_id: str, error: str) -> None: ...

    def reset(self) -> None:
        """Drops all state. Only meaningful for the in-memory store, used by tests."""
        ...
