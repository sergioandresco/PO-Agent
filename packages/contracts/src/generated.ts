/* eslint-disable */
/**
 * This file was automatically generated from services/pipeline/models (Pydantic).
 * DO NOT MODIFY IT BY HAND. Instead, change the Pydantic models and run:
 *   uv run python -m scripts.export_schemas
 *   pnpm --filter @po-agent/contracts generate
 */

/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "ArtifactStatus".
 */
export type ArtifactStatus = "draft" | "approved" | "discarded";
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Discipline".
 */
export type Discipline = "frontend" | "backend" | "database" | "infrastructure" | "qa" | "design";
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "EstimateMethod".
 */
export type EstimateMethod = "llm_reasoning" | "similarity_regression" | "hybrid";
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "JobStatus".
 */
export type JobStatus = "queued" | "running" | "completed" | "failed";
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "PipelineStage".
 */
export type PipelineStage =
  "normalize" | "segment" | "classify" | "extract_entities" | "generate_backlog" | "estimate" | "validate";

export interface AgentePoContracts {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "AcceptanceCriterion".
 */
export interface AcceptanceCriterion {
  id: string;
  given: string;
  when: string;
  then: string;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "BacklogResult".
 */
export interface BacklogResult {
  meetingId: string;
  epics: Epic[];
  features: Feature[];
  stories: UserStory[];
  generatedAt: string;
  pipelineVersion: string;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Epic".
 */
export interface Epic {
  id: string;
  title: string;
  description: string;
  status: ArtifactStatus;
  /**
   * @minItems 1
   */
  sources: [SourceReference, ...SourceReference[]];
}
/**
 * Pointer back to the source transcript. Required on every generated artifact.
 *
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "SourceReference".
 */
export interface SourceReference {
  segmentId: string;
  startCharOffset: number;
  endCharOffset: number;
  startTimeMs?: number | null;
  endTimeMs?: number | null;
  speaker?: string | null;
  verbatim: string;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Feature".
 */
export interface Feature {
  id: string;
  epicId: string;
  title: string;
  description: string;
  status: ArtifactStatus;
  /**
   * @minItems 1
   */
  sources: [SourceReference, ...SourceReference[]];
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "UserStory".
 */
export interface UserStory {
  id: string;
  featureId: string;
  title: string;
  asA: string;
  iWant: string;
  soThat: string;
  acceptanceCriteria: AcceptanceCriterion[];
  subtasks: Subtask[];
  refinement: Refinement;
  estimate?: Estimate | null;
  confidence: number;
  status: ArtifactStatus;
  /**
   * @minItems 1
   */
  sources: [SourceReference, ...SourceReference[]];
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Subtask".
 */
export interface Subtask {
  id: string;
  title: string;
  description: string;
  discipline: Discipline;
  estimatedHours?: number | null;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Refinement".
 */
export interface Refinement {
  assumptions?: string[];
  dependencies?: string[];
  risks?: string[];
  openQuestions?: string[];
  definitionOfDone?: string[];
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Estimate".
 */
export interface Estimate {
  storyPoints: 1 | 2 | 3 | 5 | 8 | 13;
  rationale: string;
  method: EstimateMethod;
  confidence: number;
}
/**
 * This interface was referenced by `AgentePoContracts`'s JSON-Schema
 * via the `definition` "Job".
 */
export interface Job {
  jobId: string;
  userId: string;
  meetingId: string;
  status: JobStatus;
  currentStage?: PipelineStage | null;
  stageTimings?: {
    [k: string]: number;
  };
  error?: string | null;
  createdAt: string;
  completedAt?: string | null;
}
