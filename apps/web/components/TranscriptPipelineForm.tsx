"use client";

import { useAuth } from "@clerk/nextjs";
import type { BacklogResult, Epic, Feature, Job, UserStory } from "@po-agent/contracts";
import { useMemo, useRef, useState } from "react";
import { createJob, getJob, getJobResult, patchArtifact } from "@/lib/api-client";
import { BacklogView } from "@/components/backlog/BacklogView";
import { JobHistoryList } from "@/components/JobHistoryList";
import { JobStatusBar } from "@/components/JobStatusBar";

const POLL_INTERVAL_MS = 2000;

export function TranscriptPipelineForm() {
  const { getToken } = useAuth();
  const [meetingId, setMeetingId] = useState("sample_meeting");
  const [transcriptText, setTranscriptText] = useState("");
  const [fileMeta, setFileMeta] = useState<{ name: string; size: number } | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<BacklogResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFormOpen, setIsFormOpen] = useState(true);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const pollTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  function stopPolling() {
    if (pollTimeout.current !== null) {
      clearTimeout(pollTimeout.current);
      pollTimeout.current = null;
    }
  }

  async function checkJob(jobId: string) {
    let current: Job;
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("No hay sesión activa");
      }
      current = await getJob(token, jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error consultando el job");
      return;
    }

    setJob(current);

    if (current.status === "completed") {
      try {
        const token = await getToken();
        if (!token) {
          throw new Error("No hay sesión activa");
        }
        setResult(await getJobResult(token, jobId));
        setHistoryRefreshKey((key) => key + 1);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error obteniendo el resultado");
      }
      return;
    }

    if (current.status === "failed") {
      setHistoryRefreshKey((key) => key + 1);
      return;
    }

    pollTimeout.current = setTimeout(() => checkJob(jobId), POLL_INTERVAL_MS);
  }

  function loadJob(jobId: string) {
    stopPolling();
    setError(null);
    setResult(null);
    setJob(null);
    setIsFormOpen(false);
    void checkJob(jobId);
  }

  async function handleUpdateArtifact(
    artifactId: string,
    updates: Record<string, unknown>,
  ) {
    try {
      const token = await getToken();
      if (!token) {
        throw new Error("No hay sesión activa");
      }
      const updated = await patchArtifact<Epic | Feature | UserStory>(
        token,
        artifactId,
        updates,
      );
      setResult((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          epics: prev.epics.map((epic) =>
            epic.id === artifactId ? (updated as Epic) : epic,
          ),
          features: prev.features.map((feature) =>
            feature.id === artifactId ? (updated as Feature) : feature,
          ),
          stories: prev.stories.map((story) =>
            story.id === artifactId ? (updated as UserStory) : story,
          ),
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error guardando el artefacto");
    }
  }

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setTranscriptText(text);
    setFileMeta({ name: file.name, size: file.size });
    const nameWithoutExtension = file.name.replace(/\.[^./]+$/, "");
    if (nameWithoutExtension) {
      setMeetingId(nameWithoutExtension);
    }
    event.target.value = "";
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    stopPolling();
    setError(null);
    setResult(null);
    setJob(null);
    setIsSubmitting(true);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("No hay sesión activa");
      }
      const created = await createJob(token, { meetingId, transcriptText });
      setJob(created);
      setIsFormOpen(false);
      pollTimeout.current = setTimeout(() => checkJob(created.jobId), POLL_INTERVAL_MS);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setIsSubmitting(false);
    }
  }

  const storyCounts = useMemo(() => {
    if (!result) return undefined;
    return {
      approved: result.stories.filter((s) => s.status === "approved").length,
      draft: result.stories.filter((s) => s.status === "draft").length,
      discarded: result.stories.filter((s) => s.status === "discarded").length,
      epics: result.epics.length,
    };
  }, [result]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_288px]">
      <div className="flex flex-col gap-4 px-6 pt-[22px] pb-10">
        {isFormOpen ? (
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-3.5 rounded-md bg-surface-2 p-[18px]"
            style={{ boxShadow: "inset 0 0 0 1px var(--color-border)" }}
          >
            <div className="flex items-baseline gap-2.5">
              <h4 className="m-0 text-[17px] font-medium">Nueva reunión</h4>
              <span className="text-[12px] text-text-5">
                pega la transcripción o sube un .txt
              </span>
              {job && (
                <button
                  type="button"
                  onClick={() => setIsFormOpen(false)}
                  className="ml-auto cursor-pointer text-[12px] text-text-5"
                >
                  Cancelar
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 items-end gap-3.5 md:grid-cols-[260px_1fr]">
              <label className="flex flex-col gap-[5px]">
                <span className="text-[11.5px] text-text-4">Meeting ID</span>
                <input
                  className="h-9 rounded-md bg-surface px-[10px] font-mono text-[13px] shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
                  value={meetingId}
                  onChange={(event) => setMeetingId(event.target.value)}
                />
              </label>
              <label className="flex flex-col gap-[5px]">
                <span className="text-[11.5px] text-text-4">
                  Archivo de transcripción (.txt)
                </span>
                <span className="flex h-9 items-center gap-2.5 rounded-md py-0 pr-[10px] pl-1 text-[13px] text-text-4 shadow-[inset_0_0_0_1px_var(--color-border)]">
                  <label className="inline-flex h-7 cursor-pointer items-center rounded-[6px] px-3 text-[12.5px] text-text-2 shadow-[inset_0_0_0_1px_var(--color-border-soft-2)]">
                    Elegir archivo
                    <input
                      type="file"
                      accept=".txt,text/plain"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  {fileMeta && (
                    <>
                      <span className="font-mono text-[12px] text-accent-soft">
                        {fileMeta.name}
                      </span>
                      <span className="ml-auto text-[11.5px] text-text-6">
                        {(fileMeta.size / 1024).toFixed(0)} KB
                      </span>
                    </>
                  )}
                </span>
              </label>
            </div>
            <span className="text-[11.5px] text-text-5">
              El archivo se lee en tu navegador, nunca se sube a ningún lado —
              solo se envía el texto al iniciar el job.
            </span>

            <label className="flex flex-col gap-[5px]">
              <span className="text-[11.5px] text-text-4">Transcripción</span>
              <textarea
                className="min-h-[150px] rounded-md bg-surface px-3 py-[11px] font-mono text-[12.5px] leading-[1.7] text-text-3 shadow-[inset_0_0_0_1px_var(--color-border)] focus:outline-none"
                rows={8}
                value={transcriptText}
                onChange={(event) => setTranscriptText(event.target.value)}
                placeholder="[00:00:03] Ana (Product Manager): ..."
              />
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={isSubmitting || !transcriptText.trim()}
                className="inline-flex h-[38px] cursor-pointer items-center rounded-md px-[18px] text-[14px] font-medium text-accent-soft shadow-[inset_0_0_0_1px_var(--color-accent)] disabled:cursor-default disabled:opacity-50"
              >
                {isSubmitting ? "Enviando…" : "Generar backlog"}
              </button>
              <span className="text-[11.5px] text-text-5">
                Formatos reconocidos:{" "}
                <span className="font-mono text-text-4">[HH:MM:SS] Hablante:</span> ·{" "}
                <span className="font-mono text-text-4">Hablante:</span> · Meet / Teams
              </span>
            </div>
          </form>
        ) : (
          <button
            type="button"
            onClick={() => setIsFormOpen(true)}
            className="flex cursor-pointer items-center gap-3 rounded-md bg-surface-2 px-[14px] py-[11px] text-left"
            style={{ boxShadow: "inset 0 0 0 1px var(--color-border)" }}
          >
            <span className="font-mono text-[12px] text-text-5">+</span>
            <span className="mr-auto text-[13.5px] font-medium">Nueva reunión</span>
            <span className="text-[12px] text-text-5">
              pegar transcripción o subir .txt
            </span>
            <span className="font-mono text-[12px] text-text-4">⌄</span>
          </button>
        )}

        {error && <p className="text-sm text-discarded-text">{error}</p>}

        {job && (
          <JobStatusBar
            job={job}
            storyCounts={storyCounts}
            onRetry={() => setIsFormOpen(true)}
            onEditTranscript={() => setIsFormOpen(true)}
          />
        )}

        {!job && (
          <div
            className="flex flex-col items-start gap-3 rounded-md px-6 py-9"
            style={{ boxShadow: "inset 0 0 0 1px var(--color-border-soft-3)" }}
          >
            <span className="font-mono text-[11.5px] tracking-[.06em] text-text-5">
              SIN BACKLOG TODAVÍA
            </span>
            <h4 className="m-0 max-w-[26ch] text-[20px] tracking-[-.015em]">
              Pega una transcripción arriba y el backlog aparece aquí.
            </h4>
            <p className="m-0 max-w-[48ch] text-[13px] text-text-4 [text-wrap:pretty]">
              Tarda entre 30 segundos y un par de minutos según el largo de la
              reunión. Puedes cerrar la pestaña: el job sigue y lo retomas
              desde &ldquo;Mis reuniones&rdquo;.
            </p>
          </div>
        )}

        {result && (
          <BacklogView result={result} onUpdateArtifact={handleUpdateArtifact} />
        )}
      </div>

      <div className="flex flex-col gap-2.5 border-l border-border-soft px-5 pt-[22px] pb-10">
        <JobHistoryList
          refreshKey={historyRefreshKey}
          selectedJobId={job?.jobId}
          onSelect={loadJob}
        />
      </div>
    </div>
  );
}
