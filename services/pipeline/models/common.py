from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for every contract model: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    DISCARDED = "discarded"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(StrEnum):
    NORMALIZE = "normalize"
    SEGMENT = "segment"
    CLASSIFY = "classify"
    EXTRACT_ENTITIES = "extract_entities"
    GENERATE_BACKLOG = "generate_backlog"
    ESTIMATE = "estimate"
    VALIDATE = "validate"


class SourceReference(ApiModel):
    """Pointer back to the source transcript. Required on every generated artifact."""

    segment_id: str
    start_char_offset: int
    end_char_offset: int
    start_time_ms: int | None = None
    end_time_ms: int | None = None
    speaker: str | None = None
    verbatim: str
