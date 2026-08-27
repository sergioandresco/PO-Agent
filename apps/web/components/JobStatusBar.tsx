"use client";

import type { Job } from "@po-agent/contracts";
import { ExportButtons } from "@/components/ExportButtons";
import { StageTimeline } from "@/components/StageTimeline";

const STATUS_LABEL: Record<Job["status"], string> = {
  queued: "En cola",
  running: "Procesando",
  completed: "Completado",
  failed: "Falló",
};

const STAGE_LABEL: Record<string, string> = {
  normalize: "normalize",
  segment: "segment",
  classify: "classify",
  extract_entities: "extract_entities",
  generate_backlog: "generate_backlog",
  estimate: "estimate",
  validate: "validate",
};

function StatusPill({ job }: { job: Job }) {
  const token = job.status === "queued" ? "draft" : job.status === "failed" ? "discarded" : job.status === "completed" ? "approved" : "running";
  return (
    <span
      className="inline-flex h-6 items-center gap-[7px] rounded-md py-[3px] pr-[10px] pl-2 text-[11.5px]"
      style={{
        background: `var(--color-${token}-wash)`,
        boxShadow: `inset 0 0 0 1px var(--color-${token}-ring)`,
        color: `var(--color-${token}-text)`,
      }}
    >
      <span
        className={`h-[7px] w-[7px] rounded-full ${job.status === "running" ? "animate-[pulse-dot_1.6s_ease-in-out_infinite]" : ""}`}
        style={{ background: `var(--color-${token})` }}
      />
      {STATUS_LABEL[job.status]}
    </span>
  );
}

export function JobStatusBar({
  job,
  storyCounts,
  onRetry,
  onEditTranscript,
}: {
  job: Job;
  storyCounts?: { approved: number; draft: number; discarded: number; epics: number };
  onRetry?: () => void;
  onEditTranscript?: () => void;
}) {
  if (job.status === "failed") {
    return (
      <div
        className="flex flex-col gap-3 rounded-md bg-surface-2 p-4"
        style={{ boxShadow: "inset 0 0 0 1px var(--color-discarded-ring)" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <StatusPill job={job} />
          <span className="text-[14px] font-medium">{job.meetingId}</span>
          <span className="font-mono text-[11.5px] text-text-5">
            job {job.jobId.replace("job_", "")} · falló en{" "}
            <span className="text-discarded-text">
              {job.currentStage ? STAGE_LABEL[job.currentStage] : "?"}
            </span>
          </span>
        </div>
        <StageTimeline currentStage={job.currentStage} failed />
        <div className="flex flex-col gap-[6px] rounded-md bg-discarded-wash-soft px-3 py-[11px]">
          <span className="text-[12.5px] text-text">{job.error}</span>
          <span className="text-[12px] text-text-4 [text-wrap:pretty]">
            Revisa que cada línea siga el formato{" "}
            <span className="font-mono text-text-2">Hablante: texto</span> y
            vuelve a intentar.
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="inline-flex h-8 cursor-pointer items-center rounded-md px-[14px] text-[13px] text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)]"
            >
              Reintentar
            </button>
          )}
          {onEditTranscript && (
            <button
              type="button"
              onClick={onEditTranscript}
              className="inline-flex h-8 cursor-pointer items-center rounded-md px-[14px] text-[13px] text-text-2 shadow-[inset_0_0_0_1px_var(--color-border-soft-2)]"
            >
              Editar transcripción
            </button>
          )}
        </div>
      </div>
    );
  }

  if (job.status === "queued" || job.status === "running") {
    return (
      <div
        className="flex flex-col gap-4 rounded-md bg-surface-2 p-4"
        style={{ boxShadow: "inset 0 0 0 1px var(--color-accent-ring)" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <StatusPill job={job} />
          <span className="text-[14px] font-medium">{job.meetingId}</span>
          <span className="font-mono text-[11.5px] text-text-5">
            job {job.jobId.replace("job_", "")}
          </span>
          <span className="ml-auto text-[12px] text-text-5">
            Actualizando cada 2 s
          </span>
        </div>
        <StageTimeline currentStage={job.currentStage} />
      </div>
    );
  }

  return (
    <div
      className="flex flex-col gap-3 rounded-md bg-surface-2 p-4"
      style={{ boxShadow: "inset 0 0 0 1px var(--color-border)" }}
    >
      <div className="flex flex-wrap items-center gap-3">
        <StatusPill job={job} />
        <span className="text-[14px] font-medium">{job.meetingId}</span>
        <span className="font-mono text-[11.5px] text-text-5">
          job {job.jobId.replace("job_", "")} · 7/7 etapas
          {job.completedAt &&
            ` · ${Math.round(
              (new Date(job.completedAt).getTime() - new Date(job.createdAt).getTime()) /
                1000,
            )}s`}
        </span>
        <div className="ml-auto flex gap-2">
          <ExportButtons jobId={job.jobId} meetingId={job.meetingId} />
        </div>
      </div>

      {storyCounts && storyCounts.approved + storyCounts.draft + storyCounts.discarded > 0 && (
        <div className="flex flex-wrap items-center gap-4 text-[12px] text-text-4">
          <span className="flex items-center gap-[6px]">
            <span className="h-[7px] w-[7px] rounded-full bg-approved" />
            {storyCounts.approved} aprobadas
          </span>
          <span className="flex items-center gap-[6px]">
            <span className="h-[7px] w-[7px] rounded-full bg-draft" />
            {storyCounts.draft} en borrador
          </span>
          <span className="flex items-center gap-[6px]">
            <span className="h-[7px] w-[7px] rounded-full bg-discarded" />
            {storyCounts.discarded} descartada{storyCounts.discarded === 1 ? "" : "s"}
          </span>
          <span className="flex h-1 max-w-[280px] flex-1 overflow-hidden rounded-full bg-border-soft">
            {(() => {
              const total = storyCounts.approved + storyCounts.draft + storyCounts.discarded;
              return (
                <>
                  <span
                    className="bg-approved"
                    style={{ width: `${(storyCounts.approved / total) * 100}%` }}
                  />
                  <span
                    className="bg-text-6"
                    style={{ width: `${(storyCounts.draft / total) * 100}%` }}
                  />
                  <span
                    className="bg-discarded"
                    style={{ width: `${(storyCounts.discarded / total) * 100}%` }}
                  />
                </>
              );
            })()}
          </span>
          <span className="text-text-5">
            {storyCounts.approved + storyCounts.draft + storyCounts.discarded} historias
            en {storyCounts.epics} {storyCounts.epics === 1 ? "épica" : "épicas"}
          </span>
        </div>
      )}
    </div>
  );
}
