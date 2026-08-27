from datetime import UTC, datetime
from typing import Literal
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

ArtifactType = Literal["epic", "feature", "story"]
Artifact = Epic | Feature | UserStory

_jobs: dict[str, Job] = {}
_results: dict[str, BacklogResult] = {}
_transcripts: dict[str, str] = {}
_artifact_index: dict[str, tuple[str, ArtifactType]] = {}


def create_job(user_id: str, meeting_id: str, transcript: str) -> Job:
    job_id = f"job_{uuid4().hex[:8]}"
    job = Job(
        job_id=job_id,
        user_id=user_id,
        meeting_id=meeting_id,
        status=JobStatus.QUEUED,
        created_at=datetime.now(UTC),
    )
    _jobs[job_id] = job
    _transcripts[job_id] = transcript
    return job


def list_jobs(user_id: str) -> list[Job]:
    return sorted(
        (job for job in _jobs.values() if job.user_id == user_id),
        key=lambda job: job.created_at,
        reverse=True,
    )


def get_job(job_id: str, user_id: str) -> Job | None:
    """Every read filters by user_id (§8: isolation is enforced in the handler,
    not just the frontend) — a user can never see another user's job, not even
    to learn it exists."""
    job = _jobs.get(job_id)
    if job is None or job.user_id != user_id:
        return None
    return job


def get_transcript(job_id: str) -> str | None:
    return _transcripts.get(job_id)


def get_result(job_id: str, user_id: str) -> BacklogResult | None:
    if get_job(job_id, user_id) is None:
        return None
    return _results.get(job_id)


def set_result(job_id: str, result: BacklogResult) -> None:
    _results[job_id] = result
    for epic in result.epics:
        _artifact_index[epic.id] = (job_id, "epic")
    for feature in result.features:
        _artifact_index[feature.id] = (job_id, "feature")
    for story in result.stories:
        _artifact_index[story.id] = (job_id, "story")


def get_artifact(artifact_id: str, user_id: str) -> tuple[str, ArtifactType, Artifact] | None:
    """Returns (job_id, artifact_type, artifact) — resolving an artifact id back to
    its job and re-checking user ownership on every call (§8)."""
    location = _artifact_index.get(artifact_id)
    if location is None:
        return None
    job_id, artifact_type = location
    if get_job(job_id, user_id) is None:
        return None
    backlog = _results.get(job_id)
    if backlog is None:
        return None

    pool: list[Artifact]
    if artifact_type == "epic":
        pool = list(backlog.epics)
    elif artifact_type == "feature":
        pool = list(backlog.features)
    else:
        pool = list(backlog.stories)

    artifact = next((item for item in pool if item.id == artifact_id), None)
    if artifact is None:
        return None
    return job_id, artifact_type, artifact


def update_artifact(job_id: str, artifact_type: ArtifactType, updated: Artifact) -> None:
    backlog = _results.get(job_id)
    if backlog is None:
        return
    if artifact_type == "epic":
        epics = [updated if e.id == updated.id else e for e in backlog.epics]
        _results[job_id] = backlog.model_copy(update={"epics": epics})
    elif artifact_type == "feature":
        features = [updated if f.id == updated.id else f for f in backlog.features]
        _results[job_id] = backlog.model_copy(update={"features": features})
    else:
        stories = [updated if s.id == updated.id else s for s in backlog.stories]
        _results[job_id] = backlog.model_copy(update={"stories": stories})


def _patch(job_id: str, **updates: object) -> None:
    job = _jobs.get(job_id)
    if job is None:
        return
    _jobs[job_id] = job.model_copy(update=updates)


def mark_running(job_id: str) -> None:
    _patch(job_id, status=JobStatus.RUNNING)


def set_stage(job_id: str, stage: PipelineStage) -> None:
    _patch(job_id, current_stage=stage)


def mark_completed(job_id: str) -> None:
    _patch(
        job_id,
        status=JobStatus.COMPLETED,
        current_stage=None,
        completed_at=datetime.now(UTC),
    )


def mark_failed(job_id: str, error: str) -> None:
    _patch(job_id, status=JobStatus.FAILED, error=error, completed_at=datetime.now(UTC))
