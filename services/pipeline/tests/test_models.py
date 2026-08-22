from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from services.pipeline.models import (
    ArtifactStatus,
    Epic,
    Job,
    JobStatus,
    PipelineStage,
    SourceReference,
)


def _source() -> SourceReference:
    return SourceReference(
        segment_id="seg_1",
        start_char_offset=0,
        end_char_offset=10,
        verbatim="hola",
    )


def test_job_serializes_with_camel_case_aliases() -> None:
    job = Job(
        job_id="job_1",
        user_id="user_1",
        meeting_id="meeting_1",
        status=JobStatus.RUNNING,
        current_stage=PipelineStage.SEGMENT,
        created_at=datetime.now(UTC),
    )
    payload = job.model_dump(by_alias=True)
    assert payload["jobId"] == "job_1"
    assert payload["currentStage"] == "segment"
    assert "job_id" not in payload


def test_job_parses_from_camel_case_payload() -> None:
    job = Job.model_validate(
        {
            "jobId": "job_1",
            "userId": "user_1",
            "meetingId": "meeting_1",
            "status": "queued",
            "createdAt": "2026-01-01T00:00:00Z",
        }
    )
    assert job.job_id == "job_1"
    assert job.status is JobStatus.QUEUED


def test_epic_rejects_empty_sources() -> None:
    with pytest.raises(ValidationError):
        Epic(
            id="epic_1",
            title="Notificaciones",
            description="...",
            status=ArtifactStatus.DRAFT,
            sources=[],
        )


def test_epic_accepts_at_least_one_source() -> None:
    epic = Epic(
        id="epic_1",
        title="Notificaciones",
        description="...",
        status=ArtifactStatus.DRAFT,
        sources=[_source()],
    )
    assert len(epic.sources) == 1


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SourceReference.model_validate(
            {
                "segmentId": "seg_1",
                "startCharOffset": 0,
                "endCharOffset": 10,
                "verbatim": "hola",
                "unexpectedField": "nope",
            }
        )
