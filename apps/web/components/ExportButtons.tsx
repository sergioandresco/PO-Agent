"use client";

import { useAuth } from "@clerk/nextjs";
import { useState } from "react";
import { exportJob, type ExportFormat } from "@/lib/api-client";

const EXTENSION_BY_FORMAT: Record<ExportFormat, string> = {
  json: "json",
  markdown: "md",
  csv: "csv",
};

const LABEL_BY_FORMAT: Record<ExportFormat, string> = {
  json: "Exportar JSON",
  markdown: "Exportar Markdown",
  csv: "Exportar CSV",
};

export function ExportButtons({
  jobId,
  meetingId,
}: {
  jobId: string;
  meetingId: string;
}) {
  const { getToken } = useAuth();
  const [pending, setPending] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExport(format: ExportFormat) {
    setPending(format);
    setError(null);
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("No hay sesión activa");
      }
      const content = await exportJob(token, jobId, format);
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${meetingId}.${EXTENSION_BY_FORMAT[format]}`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error exportando");
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {(Object.keys(LABEL_BY_FORMAT) as ExportFormat[]).map((format) => (
        <button
          key={format}
          type="button"
          onClick={() => handleExport(format)}
          disabled={pending !== null}
          className={`inline-flex h-[30px] shrink-0 cursor-pointer items-center rounded-md px-3 text-[12.5px] disabled:cursor-default disabled:opacity-50 ${
            format === "markdown"
              ? "text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)]"
              : "text-text-2 shadow-[inset_0_0_0_1px_var(--color-border-soft-2)]"
          }`}
        >
          {pending === format ? "Exportando…" : LABEL_BY_FORMAT[format]}
        </button>
      ))}
      {error && <p className="text-xs text-discarded-text">{error}</p>}
    </div>
  );
}
