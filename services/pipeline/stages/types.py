from enum import StrEnum

from pydantic import BaseModel, Field

from services.pipeline.models import Discipline


class Utterance(BaseModel):
    """One speaker turn parsed out of a raw transcript, with its exact byte span
    in the original text. This is the only place offsets get computed — every
    SourceReference downstream is built from these, never from LLM output."""

    index: int
    speaker: str | None
    timestamp_ms: int | None
    text: str
    start_char_offset: int
    end_char_offset: int


class Segment(BaseModel):
    id: str
    title: str
    utterances: list[Utterance]


class UtteranceLabel(StrEnum):
    REQUIREMENT = "requirement"
    RISK = "risk"
    DECISION = "decision"
    CONSTRAINT = "constraint"
    QUESTION = "question"
    OFF_TOPIC = "off_topic"


class ClassifiedUtterance(BaseModel):
    utterance_index: int
    label: UtteranceLabel


class AcceptanceCriterionCandidate(BaseModel):
    given: str
    when: str
    then: str


class SubtaskCandidate(BaseModel):
    title: str
    description: str
    discipline: Discipline
    estimated_hours: float | None = None


class StoryCandidate(BaseModel):
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: list[AcceptanceCriterionCandidate] = Field(min_length=1)
    subtasks: list[SubtaskCandidate] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    supporting_utterance_indices: list[int] = Field(min_length=1)


class RefinementCandidate(BaseModel):
    assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)


class FeatureGroup(BaseModel):
    title: str
    description: str
    story_indices: list[int] = Field(min_length=1)


class EpicGroup(BaseModel):
    title: str
    description: str
    features: list[FeatureGroup] = Field(min_length=1)


class StoryRefinementEntry(BaseModel):
    story_index: int
    refinement: RefinementCandidate


class BacklogOrganization(BaseModel):
    epics: list[EpicGroup] = Field(min_length=1)
    story_refinements: list[StoryRefinementEntry] = Field(default_factory=list)
