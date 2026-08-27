import type { PipelineStage } from "@po-agent/contracts";

const STAGES: { key: PipelineStage; label: string }[] = [
  { key: "normalize", label: "Normalizar" },
  { key: "segment", label: "Segmentar" },
  { key: "classify", label: "Clasificar" },
  { key: "extract_entities", label: "Entidades" },
  { key: "generate_backlog", label: "Generar backlog" },
  { key: "estimate", label: "Estimar" },
  { key: "validate", label: "Validar" },
];

export function StageTimeline({
  currentStage,
  failed = false,
}: {
  currentStage: PipelineStage | null | undefined;
  failed?: boolean;
}) {
  const currentIndex = currentStage
    ? STAGES.findIndex((stage) => stage.key === currentStage)
    : STAGES.length;
  const progressPercent =
    STAGES.length > 1 ? (Math.max(currentIndex, 0) / (STAGES.length - 1)) * 100 : 0;

  return (
    <div className="relative grid grid-cols-4 gap-y-4 sm:grid-cols-7 sm:gap-y-0">
      <div className="absolute top-[6px] right-[6%] left-[6%] hidden h-px bg-border-soft-2 sm:block" />
      <div
        className="absolute top-[6px] left-[6%] hidden h-px bg-accent sm:block"
        style={{ width: `${Math.min(progressPercent * 0.88, 88)}%` }}
      />
      {STAGES.map((stage, i) => {
        const isDone = i < currentIndex;
        const isCurrent = i === currentIndex && !failed;
        const isFailedHere = failed && i === currentIndex;

        return (
          <div key={stage.key} className="relative flex flex-col items-start gap-[9px]">
            <span
              className={`h-[13px] w-[13px] shrink-0 rounded-full ${isCurrent ? "animate-[pulse-dot_1.6s_ease-in-out_infinite]" : ""}`}
              style={{
                background:
                  isFailedHere || isDone ? "var(--color-accent)" : "var(--color-surface-2)",
                ...(isFailedHere && { background: "var(--color-discarded)" }),
                boxShadow:
                  isDone || isFailedHere
                    ? "0 0 0 3px var(--color-surface-2)"
                    : isCurrent
                      ? "0 0 0 2px var(--color-accent-soft), 0 0 0 6px var(--color-accent-wash-2)"
                      : "inset 0 0 0 1px var(--color-text-6)",
              }}
            />
            <span
              className={`text-[12px] ${
                isCurrent
                  ? "font-medium text-accent-pale"
                  : isFailedHere
                    ? "text-discarded-text"
                    : isDone
                      ? "text-text-2"
                      : "text-text-5"
              }`}
            >
              {stage.label}
            </span>
            <span
              className={`font-mono text-[10px] ${isCurrent ? "text-accent-strong" : "text-text-6"}`}
            >
              {stage.key}
            </span>
          </div>
        );
      })}
    </div>
  );
}
