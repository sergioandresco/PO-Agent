"""Export the Pydantic models (source of truth) to a consolidated JSON Schema file.

Usage: python -m scripts.export_schemas
The output feeds packages/contracts' `generate` script (json-schema-to-typescript),
which turns it into the TypeScript types the frontend consumes. Never edit the
generated TypeScript by hand: change the Pydantic models and re-run both steps.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, models_json_schema
from services.pipeline.models import (
    AcceptanceCriterion,
    BacklogResult,
    Epic,
    Estimate,
    Feature,
    Job,
    Refinement,
    SourceReference,
    Subtask,
    UserStory,
)

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "schemas" / "backlog.schema.json"

ROOT_MODELS: list[type[BaseModel]] = [
    Job,
    SourceReference,
    Epic,
    Feature,
    AcceptanceCriterion,
    Subtask,
    Refinement,
    Estimate,
    UserStory,
    BacklogResult,
]

MODEL_SPECS: list[tuple[type[BaseModel], JsonSchemaMode]] = [
    (model, "serialization") for model in ROOT_MODELS
]


class CleanGenerateJsonSchema(GenerateJsonSchema):
    """Suppress per-field titles so json-schema-to-typescript inlines scalar types
    instead of hoisting a standalone type alias for every property."""

    def field_title_should_be_set(self, schema: Any) -> bool:
        return False


def main() -> None:
    _, top_level_schema = models_json_schema(
        MODEL_SPECS,
        title="AgentePoContracts",
        schema_generator=CleanGenerateJsonSchema,
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(top_level_schema, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(top_level_schema.get('$defs', {}))} type definitions to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
