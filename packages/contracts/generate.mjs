import { compileFromFile } from "json-schema-to-typescript";
import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const schemaPath = path.join(dirname, "../../docs/schemas/backlog.schema.json");
const outPath = path.join(dirname, "src/generated.ts");

const banner = `/* eslint-disable */
/**
 * This file was automatically generated from services/pipeline/models (Pydantic).
 * DO NOT MODIFY IT BY HAND. Instead, change the Pydantic models and run:
 *   uv run python -m scripts.export_schemas
 *   pnpm --filter @po-agent/contracts generate
 */

`;

const ts = await compileFromFile(schemaPath, {
  unreachableDefinitions: true,
  bannerComment: "",
});

writeFileSync(outPath, banner + ts);
console.log(`Wrote ${outPath}`);
