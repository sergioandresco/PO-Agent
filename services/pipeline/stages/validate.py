from services.pipeline.models import BacklogResult


def validate(backlog: BacklogResult) -> BacklogResult:
    """Final integrity gate (§5's invariant rule): drops any artifact without
    sources — impossible to construct via the Pydantic models directly, but this
    also catches structural orphans (a feature pointing at a dropped epic, etc.)
    that could slip in during consolidation."""
    valid_epics = [epic for epic in backlog.epics if epic.sources]
    valid_epic_ids = {epic.id for epic in valid_epics}

    valid_features = [
        feature
        for feature in backlog.features
        if feature.sources and feature.epic_id in valid_epic_ids
    ]
    valid_feature_ids = {feature.id for feature in valid_features}

    valid_stories = [
        story
        for story in backlog.stories
        if story.sources and story.feature_id in valid_feature_ids
    ]

    return backlog.model_copy(
        update={"epics": valid_epics, "features": valid_features, "stories": valid_stories}
    )
