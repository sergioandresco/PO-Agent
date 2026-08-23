from datetime import UTC, datetime

from services.pipeline.models import (
    ArtifactStatus,
    BacklogResult,
    Epic,
    Feature,
    Refinement,
    SourceReference,
    UserStory,
)
from services.pipeline.stages.validate import validate


def _source() -> SourceReference:
    return SourceReference(
        segment_id="seg_1", start_char_offset=0, end_char_offset=10, verbatim="hola"
    )


def _story(story_id: str, feature_id: str) -> UserStory:
    return UserStory(
        id=story_id,
        feature_id=feature_id,
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


def test_validate_drops_features_pointing_at_a_missing_epic() -> None:
    epic = Epic(
        id="epic_1", title="t", description="d", status=ArtifactStatus.DRAFT, sources=[_source()]
    )
    orphan_feature = Feature(
        id="feature_orphan",
        epic_id="epic_does_not_exist",
        title="t",
        description="d",
        status=ArtifactStatus.DRAFT,
        sources=[_source()],
    )
    real_feature = Feature(
        id="feature_1",
        epic_id="epic_1",
        title="t",
        description="d",
        status=ArtifactStatus.DRAFT,
        sources=[_source()],
    )
    orphan_story = _story("story_orphan", feature_id="feature_orphan")
    real_story = _story("story_1", feature_id="feature_1")

    backlog = BacklogResult(
        meeting_id="m1",
        epics=[epic],
        features=[orphan_feature, real_feature],
        stories=[orphan_story, real_story],
        generated_at=datetime.now(UTC),
        pipeline_version="test",
    )

    result = validate(backlog)

    assert [f.id for f in result.features] == ["feature_1"]
    assert [s.id for s in result.stories] == ["story_1"]


def test_validate_keeps_a_fully_grounded_backlog_untouched() -> None:
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
    story = _story("story_1", feature_id="feature_1")

    backlog = BacklogResult(
        meeting_id="m1",
        epics=[epic],
        features=[feature],
        stories=[story],
        generated_at=datetime.now(UTC),
        pipeline_version="test",
    )

    result = validate(backlog)

    assert len(result.epics) == 1
    assert len(result.features) == 1
    assert len(result.stories) == 1
