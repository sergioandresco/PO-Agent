from pydantic.json_schema import models_json_schema
from scripts.export_schemas import MODEL_SPECS, CleanGenerateJsonSchema

EXPECTED_DEFS = {
    "AcceptanceCriterion",
    "ArtifactStatus",
    "BacklogResult",
    "Discipline",
    "Epic",
    "Estimate",
    "EstimateMethod",
    "Feature",
    "Job",
    "JobStatus",
    "PipelineStage",
    "Refinement",
    "SourceReference",
    "Subtask",
    "UserStory",
}


def test_exported_schema_contains_every_contract_type() -> None:
    _, schema = models_json_schema(MODEL_SPECS, schema_generator=CleanGenerateJsonSchema)
    assert set(schema["$defs"].keys()) == EXPECTED_DEFS


def test_field_titles_are_suppressed_for_clean_ts_output() -> None:
    _, schema = models_json_schema(MODEL_SPECS, schema_generator=CleanGenerateJsonSchema)
    acceptance_criterion = schema["$defs"]["AcceptanceCriterion"]
    assert "title" not in acceptance_criterion["properties"]["id"]
