from datetime import datetime

from pydantic import Field

from .common import ApiModel, JobStatus, PipelineStage


class Job(ApiModel):
    job_id: str
    user_id: str
    meeting_id: str
    status: JobStatus
    current_stage: PipelineStage | None = None
    stage_timings: dict[PipelineStage, float] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
