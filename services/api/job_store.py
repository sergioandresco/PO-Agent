"""Module-level facade over the configured JobStore.

Callers (handlers/, the worker, the local server) import these functions and
never learn whether they are talking to memory or to DynamoDB. The backend is
resolved lazily on first use so that importing this module never requires AWS
configuration — that is what keeps the test suite runnable with no environment.
"""

from services.pipeline.models import BacklogResult, Job, PipelineStage

from .stores import InMemoryJobStore
from .stores.base import Artifact, ArtifactType, JobStore
from .stores.dynamo import from_environment

_store: JobStore | None = None


def store() -> JobStore:
    global _store
    if _store is None:
        _store = from_environment() or InMemoryJobStore()
    return _store


def use_store(new_store: JobStore | None) -> None:
    """Swaps the backend. Tests use it to force a clean store between cases."""
    global _store
    _store = new_store


def reset() -> None:
    store().reset()


def create_job(user_id: str, meeting_id: str, transcript: str) -> Job:
    return store().create_job(user_id, meeting_id, transcript)


def list_jobs(user_id: str) -> list[Job]:
    return store().list_jobs(user_id)


def get_job(job_id: str, user_id: str) -> Job | None:
    return store().get_job(job_id, user_id)


def get_transcript(job_id: str) -> str | None:
    return store().get_transcript(job_id)


def get_result(job_id: str, user_id: str) -> BacklogResult | None:
    return store().get_result(job_id, user_id)


def set_result(job_id: str, user_id: str, result: BacklogResult) -> None:
    store().set_result(job_id, user_id, result)


def get_artifact(
    artifact_id: str, user_id: str
) -> tuple[str, ArtifactType, Artifact] | None:
    return store().get_artifact(artifact_id, user_id)


def update_artifact(
    job_id: str, user_id: str, artifact_type: ArtifactType, updated: Artifact
) -> None:
    store().update_artifact(job_id, user_id, artifact_type, updated)


def mark_running(job_id: str, user_id: str) -> None:
    store().mark_running(job_id, user_id)


def set_stage(job_id: str, user_id: str, stage: PipelineStage) -> None:
    store().set_stage(job_id, user_id, stage)


def mark_completed(job_id: str, user_id: str) -> None:
    store().mark_completed(job_id, user_id)


def mark_failed(job_id: str, user_id: str, error: str) -> None:
    store().mark_failed(job_id, user_id, error)


__all__ = [
    "Artifact",
    "ArtifactType",
    "create_job",
    "get_artifact",
    "get_job",
    "get_result",
    "get_transcript",
    "list_jobs",
    "mark_completed",
    "mark_failed",
    "mark_running",
    "reset",
    "set_result",
    "set_stage",
    "store",
    "update_artifact",
    "use_store",
]
