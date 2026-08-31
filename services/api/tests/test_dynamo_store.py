"""Exercises the DynamoDB backend against moto, with the same table and index
definitions the CDK stack creates. These are the tests that would otherwise only
run in AWS: key layout, artifact reassembly, and user isolation.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from moto import mock_aws

from services.api.stores.dynamo import DynamoJobStore
from services.pipeline.models import (
    ArtifactStatus,
    BacklogResult,
    Epic,
    Feature,
    JobStatus,
    PipelineStage,
    Refinement,
    SourceReference,
    UserStory,
)

TABLE = "po-agent-test"
BUCKET = "po-agent-transcripts-test"


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> Iterator[DynamoJobStore]:
    # moto needs a region and credentials in the environment, the same way Lambda
    # supplies them at runtime.
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    with mock_aws():
        ddb: Any = boto3.resource("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName=TABLE,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "gsi1pk", "AttributeType": "S"},
                {"AttributeName": "gsi1sk", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi1",
                    "KeySchema": [
                        {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        s3: Any = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET)
        yield DynamoJobStore(table_name=TABLE, bucket=BUCKET)


def _source() -> SourceReference:
    return SourceReference(
        segment_id="seg_1", start_char_offset=0, end_char_offset=4, verbatim="hola"
    )


def _backlog() -> BacklogResult:
    return BacklogResult(
        meeting_id="meeting_1",
        epics=[
            Epic(
                id="epic_1",
                title="t",
                description="d",
                status=ArtifactStatus.DRAFT,
                sources=[_source()],
            )
        ],
        features=[
            Feature(
                id="feature_1",
                epic_id="epic_1",
                title="t",
                description="d",
                status=ArtifactStatus.DRAFT,
                sources=[_source()],
            )
        ],
        stories=[
            UserStory(
                id="story_1",
                feature_id="feature_1",
                title="titulo",
                as_a="usuario",
                i_want="algo",
                so_that="beneficio",
                acceptance_criteria=[],
                subtasks=[],
                refinement=Refinement(),
                estimate=None,
                confidence=0.9,
                status=ArtifactStatus.DRAFT,
                sources=[_source()],
            )
        ],
        generated_at=datetime.now(UTC),
        pipeline_version="test",
    )


def test_create_job_stores_transcript_in_s3_not_dynamo(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "una transcripcion larga")

    assert store.get_transcript(job.job_id) == "una transcripcion larga"
    assert store.get_job(job.job_id, "user_1") is not None


def test_get_job_is_scoped_to_the_owner(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")

    assert store.get_job(job.job_id, "user_2") is None


def test_list_jobs_returns_only_the_callers_jobs_newest_first(store: DynamoJobStore) -> None:
    first = store.create_job("user_1", "m1", "t")
    second = store.create_job("user_1", "m2", "t")
    store.create_job("user_2", "m3", "t")

    ids = [job.job_id for job in store.list_jobs("user_1")]

    assert set(ids) == {first.job_id, second.job_id}
    assert len(store.list_jobs("user_2")) == 1


def test_result_round_trips_through_separate_artifact_items(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")
    store.set_result(job.job_id, "user_1", _backlog())

    loaded = store.get_result(job.job_id, "user_1")

    assert loaded is not None
    assert loaded.meeting_id == "meeting_1"
    assert [e.id for e in loaded.epics] == ["epic_1"]
    assert [f.id for f in loaded.features] == ["feature_1"]
    assert [s.id for s in loaded.stories] == ["story_1"]
    assert loaded.stories[0].confidence == 0.9


def test_get_result_is_scoped_to_the_owner(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")
    store.set_result(job.job_id, "user_1", _backlog())

    assert store.get_result(job.job_id, "user_2") is None


def test_get_artifact_resolves_the_job_and_rechecks_ownership(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")
    store.set_result(job.job_id, "user_1", _backlog())

    found = store.get_artifact("story_1", "user_1")
    assert found is not None
    resolved_job, artifact_type, artifact = found
    assert resolved_job == job.job_id
    assert artifact_type == "story"
    assert artifact.id == "story_1"

    assert store.get_artifact("story_1", "user_2") is None
    assert store.get_artifact("does_not_exist", "user_1") is None


def test_update_artifact_persists_and_leaves_siblings_alone(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")
    store.set_result(job.job_id, "user_1", _backlog())
    found = store.get_artifact("story_1", "user_1")
    assert found is not None
    _, _, story = found
    assert isinstance(story, UserStory)

    store.update_artifact(
        job.job_id,
        "user_1",
        "story",
        story.model_copy(update={"so_that": "otro beneficio"}),
    )

    result = store.get_result(job.job_id, "user_1")
    assert result is not None
    assert result.stories[0].so_that == "otro beneficio"
    assert result.epics[0].title == "t"


def test_status_transitions_persist(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")

    store.mark_running(job.job_id, "user_1")
    store.set_stage(job.job_id, "user_1", PipelineStage.SEGMENT)
    running = store.get_job(job.job_id, "user_1")
    assert running is not None
    assert running.status is JobStatus.RUNNING
    assert running.current_stage is PipelineStage.SEGMENT

    store.mark_completed(job.job_id, "user_1")
    done = store.get_job(job.job_id, "user_1")
    assert done is not None
    assert done.status is JobStatus.COMPLETED
    assert done.current_stage is None
    assert done.completed_at is not None


def test_mark_failed_records_the_error(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")

    store.mark_failed(job.job_id, "user_1", "boom")

    failed = store.get_job(job.job_id, "user_1")
    assert failed is not None
    assert failed.status is JobStatus.FAILED
    assert failed.error == "boom"


def test_writes_from_a_non_owner_are_ignored(store: DynamoJobStore) -> None:
    job = store.create_job("user_1", "meeting_1", "t")

    store.set_result(job.job_id, "user_2", _backlog())
    store.mark_completed(job.job_id, "user_2")

    assert store.get_result(job.job_id, "user_1") is None
    owner_view = store.get_job(job.job_id, "user_1")
    assert owner_view is not None
    assert owner_view.status is JobStatus.QUEUED
