"use client";

import { useAuth } from "@clerk/nextjs";
import type { Job } from "@po-agent/contracts";
import { useEffect, useState } from "react";
import { listJobs } from "@/lib/api-client";

const STATUS_LABELS: Record<Job["status"], string> = {
  queued: "En cola",
  running: "Procesando",
  completed: "Completado",
  failed: "Falló",
};

const STATUS_DOT: Record<Job["status"], string> = {
  queued: "var(--color-draft)",
  running: "var(--color-running)",
  completed: "var(--color-approved)",
  failed: "var(--color-discarded)",
};

export function JobHistoryList({
  refreshKey,
  selectedJobId,
  onSelect,
}: {
  refreshKey: number;
  selectedJobId?: string;
  onSelect: (jobId: string) => void;
}) {
  const { getToken } = useAuth();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const token = await getToken();
        if (!token) return;
        const fetched = await listJobs(token);
        if (!cancelled) {
          setJobs(fetched);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Error cargando reuniones");
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey]);

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-baseline gap-2">
        <span className="text-[11px] tracking-[.1em] text-text-4 uppercase">
          Mis reuniones
        </span>
        <span className="ml-auto font-mono text-[11px] text-text-6">
          {jobs.length || ""}
        </span>
      </div>

      {error && <p className="text-[12.5px] text-discarded-text">{error}</p>}

      {!error && jobs.length === 0 && (
        <div
          className="flex flex-col gap-2 rounded-md px-[14px] py-[18px]"
          style={{ boxShadow: "inset 0 0 0 1px var(--color-border-soft)" }}
        >
          <span className="font-mono text-xs text-text-6">—</span>
          <span className="text-[13px] text-text-2">
            Todavía no hay reuniones procesadas.
          </span>
          <span className="text-[12px] text-text-5 [text-wrap:pretty]">
            La primera aparecerá aquí en cuanto generes un backlog; puedes
            volver a ella sin correr el pipeline otra vez.
          </span>
        </div>
      )}

      <div className="flex flex-col gap-[6px]">
        {jobs.map((job) => (
          <button
            key={job.jobId}
            type="button"
            onClick={() => onSelect(job.jobId)}
            className="flex cursor-pointer flex-col gap-[5px] rounded-md px-3 py-[10px] text-left"
            style={{
              background:
                job.jobId === selectedJobId ? "var(--color-surface)" : "transparent",
              boxShadow: `inset 0 0 0 1px ${
                job.jobId === selectedJobId
                  ? "var(--color-accent-ring)"
                  : "var(--color-border-soft)"
              }`,
            }}
          >
            <div className="flex items-center gap-2">
              <span
                className="h-[6px] w-[6px] shrink-0 rounded-full"
                style={{ background: STATUS_DOT[job.status] }}
              />
              <span
                className={`text-[13px] ${job.jobId === selectedJobId ? "font-medium" : "text-text-2"}`}
              >
                {job.meetingId}
              </span>
            </div>
            <span className="font-mono text-[10.5px] text-text-5">
              {STATUS_LABELS[job.status]} ·{" "}
              {new Date(job.createdAt).toLocaleString("es", {
                day: "2-digit",
                month: "short",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
