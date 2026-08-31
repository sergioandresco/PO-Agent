from typing import Any

from services.pipeline.models import Epic, Feature, UserStory

from .. import job_store
from ..job_store import Artifact, ArtifactType

_IMMUTABLE_FIELDS = {"id", "sources", "epicId", "featureId"}

_MODEL_BY_TYPE: dict[ArtifactType, type[Epic] | type[Feature] | type[UserStory]] = {
    "epic": Epic,
    "feature": Feature,
    "story": UserStory,
}


def patch_artifact(
    user_id: str, artifact_id: str, updates: dict[str, Any]
) -> Artifact | None:
    """Merges `updates` onto the current artifact and re-validates the whole thing
    against its Pydantic model — a PO can edit content and status, but never the
    id, the foreign keys, or `sources` (that's the trace back to the transcript;
    editing it by hand would defeat the whole point, §1)."""
    location = job_store.get_artifact(artifact_id, user_id)
    if location is None:
        return None
    job_id, artifact_type, current = location

    safe_updates = {key: value for key, value in updates.items() if key not in _IMMUTABLE_FIELDS}
    merged = current.model_dump(by_alias=True)
    merged.update(safe_updates)

    model_cls = _MODEL_BY_TYPE[artifact_type]
    updated = model_cls.model_validate(merged)

    job_store.update_artifact(job_id, user_id, artifact_type, updated)
    return updated
