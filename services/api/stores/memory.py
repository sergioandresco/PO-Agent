"""In-memory store. Backs local development and the whole test suite.

State lives for the life of the process, which is exactly what a dev server and
a pytest run want, and exactly what production must not have — see dynamo.py.
"""

from datetime import UTC, datetime
from uuid import uuid4

from services.pipeline.models import BacklogResult, Job, JobStatus, PipelineStage

from .base import Artifact, ArtifactType


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._results: dict[str, BacklogResult] = {}
        self._transcripts: dict[str, str] = {}
        self._artifact_index: dict[str, tuple[str, ArtifactType]] = {}

    def reset(self) -> None:
        self._jobs.clear()
        self._results.clear()
        self._transcripts.clear()
        self._artifact_index.clear()

    def create_job(self, user_id: str, meeting_id: str, transcript: str) -> Job:
        job_id = f"job_{uuid4().hex[:8]}"
        job = Job(
            job_id=job_id,
            user_id=user_id,
            meeting_id=meeting_id,
            status=JobStatus.QUEUED,
            created_at=datetime.now(UTC),
        )
        self._jobs[job_id] = job
        self._transcripts[job_id] = transcript
        return job

    def list_jobs(self, user_id: str) -> list[Job]:
        return sorted(
            (job for job in self._jobs.values() if job.user_id == user_id),
            key=lambda job: job.created_at,
            reverse=True,
        )

    def get_job(self, job_id: str, user_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return job

    def get_transcript(self, job_id: str) -> str | None:
        return self._transcripts.get(job_id)

    def get_result(self, job_id: str, user_id: str) -> BacklogResult | None:
        if self.get_job(job_id, user_id) is None:
            return None
        return self._results.get(job_id)

    def set_result(self, job_id: str, user_id: str, result: BacklogResult) -> None:
        if self.get_job(job_id, user_id) is None:
            return
        self._results[job_id] = result
        for epic in result.epics:
            self._artifact_index[epic.id] = (job_id, "epic")
        for feature in result.features:
            self._artifact_index[feature.id] = (job_id, "feature")
        for story in result.stories:
            self._artifact_index[story.id] = (job_id, "story")

    def get_artifact(
        self, artifact_id: str, user_id: str
    ) -> tuple[str, ArtifactType, Artifact] | None:
        location = self._artifact_index.get(artifact_id)
        if location is None:
            return None
        job_id, artifact_type = location
        if self.get_job(job_id, user_id) is None:
            return None
        backlog = self._results.get(job_id)
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

    def update_artifact(
        self, job_id: str, user_id: str, artifact_type: ArtifactType, updated: Artifact
    ) -> None:
        if self.get_job(job_id, user_id) is None:
            return
        backlog = self._results.get(job_id)
        if backlog is None:
            return
        if artifact_type == "epic":
            epics = [updated if e.id == updated.id else e for e in backlog.epics]
            self._results[job_id] = backlog.model_copy(update={"epics": epics})
        elif artifact_type == "feature":
            features = [updated if f.id == updated.id else f for f in backlog.features]
            self._results[job_id] = backlog.model_copy(update={"features": features})
        else:
            stories = [updated if s.id == updated.id else s for s in backlog.stories]
            self._results[job_id] = backlog.model_copy(update={"stories": stories})

    def _patch(self, job_id: str, user_id: str, **updates: object) -> None:
        job = self.get_job(job_id, user_id)
        if job is None:
            return
        self._jobs[job_id] = job.model_copy(update=updates)

    def mark_running(self, job_id: str, user_id: str) -> None:
        self._patch(job_id, user_id, status=JobStatus.RUNNING)

    def set_stage(self, job_id: str, user_id: str, stage: PipelineStage) -> None:
        self._patch(job_id, user_id, current_stage=stage)

    def mark_completed(self, job_id: str, user_id: str) -> None:
        self._patch(
            job_id,
            user_id,
            status=JobStatus.COMPLETED,
            current_stage=None,
            completed_at=datetime.now(UTC),
        )

    def mark_failed(self, job_id: str, user_id: str, error: str) -> None:
        self._patch(
            job_id,
            user_id,
            status=JobStatus.FAILED,
            error=error,
            completed_at=datetime.now(UTC),
        )
