from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from services.api import job_store
from services.api.auth import require_user_id
from services.api.local_server import app
from services.pipeline.models import (
    ArtifactStatus,
    BacklogResult,
    Epic,
    Feature,
    Refinement,
    SourceReference,
    UserStory,
)


@pytest.fixture(autouse=True)
def _clean_job_store() -> Iterator[None]:
    job_store._jobs.clear()
    job_store._results.clear()
    job_store._transcripts.clear()
    job_store._artifact_index.clear()
    yield
    app.dependency_overrides.clear()


def _source() -> SourceReference:
    return SourceReference(
        segment_id="seg_1", start_char_offset=0, end_char_offset=10, verbatim="hola"
    )


def _seed_completed_job(user_id: str) -> tuple[str, str, str, str]:
    job = job_store.create_job(user_id, "meeting_1", "raw transcript")
    epic = Epic(
        id="epic_1", title="t", description="d", status=ArtifactStatus.DRAFT, sources=[_source()]
    )
    feature = Feature(
        id="feature_1",
        epic_id="epic_1",
        title="t",
        description="d",
        status=ArtifactStatus.DRAFT,
        sources=[_source()],
    )
    story = UserStory(
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
    backlog = BacklogResult(
        meeting_id="meeting_1",
        epics=[epic],
        features=[feature],
        stories=[story],
        generated_at=datetime.now(UTC),
        pipeline_version="test",
    )
    job_store.set_result(job.job_id, backlog)
    job_store.mark_completed(job.job_id)
    return job.job_id, epic.id, feature.id, story.id


def _client_as(user_id: str) -> TestClient:
    app.dependency_overrides[require_user_id] = lambda: user_id
    return TestClient(app)


def test_patch_story_updates_content_and_status() -> None:
    _, _, _, story_id = _seed_completed_job("user_1")
    client = _client_as("user_1")

    response = client.patch(
        f"/artifacts/{story_id}", json={"soThat": "algo mejor", "status": "approved"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["soThat"] == "algo mejor"
    assert body["status"] == "approved"
    assert body["id"] == story_id


def test_patch_epic_and_feature_serialize_correctly() -> None:
    _, epic_id, feature_id, _ = _seed_completed_job("user_1")
    client = _client_as("user_1")

    epic_response = client.patch(f"/artifacts/{epic_id}", json={"title": "Nuevo titulo epic"})
    assert epic_response.status_code == 200
    assert epic_response.json()["title"] == "Nuevo titulo epic"
    assert "epicId" not in epic_response.json()

    feature_response = client.patch(
        f"/artifacts/{feature_id}", json={"title": "Nuevo titulo feature"}
    )
    assert feature_response.status_code == 200
    assert feature_response.json()["title"] == "Nuevo titulo feature"
    assert feature_response.json()["epicId"] == epic_id


def test_patch_ignores_attempts_to_edit_sources_or_ids() -> None:
    _, _, _, story_id = _seed_completed_job("user_1")
    client = _client_as("user_1")

    response = client.patch(
        f"/artifacts/{story_id}", json={"sources": [], "id": "hacked", "featureId": "hacked"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["sources"]) == 1
    assert body["id"] == story_id
    assert body["featureId"] == "feature_1"


def test_patch_unknown_artifact_returns_404() -> None:
    client = _client_as("user_1")
    response = client.patch("/artifacts/does_not_exist", json={"title": "x"})
    assert response.status_code == 404


def test_get_job_enforces_user_isolation() -> None:
    job_id, *_ = _seed_completed_job("user_1")
    other_users_client = _client_as("user_2")

    response = other_users_client.get(f"/jobs/{job_id}")

    assert response.status_code == 404


def test_patch_artifact_enforces_user_isolation() -> None:
    _, epic_id, _, _ = _seed_completed_job("user_1")
    other_users_client = _client_as("user_2")

    response = other_users_client.patch(f"/artifacts/{epic_id}", json={"title": "hijacked"})

    assert response.status_code == 404


def test_list_jobs_returns_only_the_caller_s_jobs() -> None:
    job_id, *_ = _seed_completed_job("user_1")
    job_store.create_job("user_2", "meeting_2", "transcript")

    response = _client_as("user_1").get("/jobs")

    assert response.status_code == 200
    job_ids = [job["jobId"] for job in response.json()]
    assert job_ids == [job_id]


def test_export_json_matches_the_result_endpoint() -> None:
    job_id, *_ = _seed_completed_job("user_1")
    client = _client_as("user_1")

    result_response = client.get(f"/jobs/{job_id}/result")
    export_response = client.get(f"/jobs/{job_id}/export?format=json")

    assert export_response.status_code == 200
    assert export_response.json() == result_response.json()


def test_export_markdown_contains_story_title_and_source_quote() -> None:
    job_id, *_ = _seed_completed_job("user_1")
    client = _client_as("user_1")

    response = client.get(f"/jobs/{job_id}/export?format=markdown")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    body = response.text
    assert "# Backlog: meeting_1" in body
    assert "usuario" in body
    assert "hola" in body


def test_export_csv_has_one_row_per_story() -> None:
    job_id, *_ = _seed_completed_job("user_1")
    client = _client_as("user_1")

    response = client.get(f"/jobs/{job_id}/export?format=csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    rows = response.text.strip().splitlines()
    assert len(rows) == 2
    assert "story_1" not in rows[0]
    assert "usuario" in rows[1]
