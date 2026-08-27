from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field

from .common import ApiModel, ArtifactStatus, SourceReference


class Epic(ApiModel):
    id: str
    title: str
    description: str
    status: ArtifactStatus
    sources: list[SourceReference] = Field(min_length=1)


class Feature(ApiModel):
    id: str
    epic_id: str
    title: str
    description: str
    status: ArtifactStatus
    sources: list[SourceReference] = Field(min_length=1)


class AcceptanceCriterion(ApiModel):
    id: str
    given: str
    when: str
    then: str


class Discipline(StrEnum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    QA = "qa"
    DESIGN = "design"


class Subtask(ApiModel):
    id: str
    title: str
    description: str
    discipline: Discipline
    estimated_hours: float | None = None


class Refinement(ApiModel):
    assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)


class EstimateMethod(StrEnum):
    LLM_REASONING = "llm_reasoning"
    SIMILARITY_REGRESSION = "similarity_regression"
    HYBRID = "hybrid"


class Estimate(ApiModel):
    story_points: Literal[1, 2, 3, 5, 8, 13]
    rationale: str
    method: EstimateMethod
    confidence: float = Field(ge=0, le=1)


class UserStory(ApiModel):
    id: str
    feature_id: str
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: list[AcceptanceCriterion]
    subtasks: list[Subtask]
    refinement: Refinement
    estimate: Estimate | None = None
    confidence: float = Field(ge=0, le=1)
    status: ArtifactStatus
    sources: list[SourceReference] = Field(min_length=1)


class BacklogResult(ApiModel):
    meeting_id: str
    epics: list[Epic]
    features: list[Feature]
    stories: list[UserStory]
    generated_at: datetime
    pipeline_version: str
