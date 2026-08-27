import type { BacklogResult, Job } from "@po-agent/contracts";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:3001";

async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail ?? `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createJob(
  token: string,
  input: { meetingId: string; transcriptText: string },
): Promise<Job> {
  return apiFetch<Job>("/jobs", token, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listJobs(token: string): Promise<Job[]> {
  return apiFetch<Job[]>("/jobs", token);
}

export function getJob(token: string, jobId: string): Promise<Job> {
  return apiFetch<Job>(`/jobs/${jobId}`, token);
}

export function getJobResult(
  token: string,
  jobId: string,
): Promise<BacklogResult> {
  return apiFetch<BacklogResult>(`/jobs/${jobId}/result`, token);
}

export function patchArtifact<T>(
  token: string,
  artifactId: string,
  updates: Record<string, unknown>,
): Promise<T> {
  return apiFetch<T>(`/artifacts/${artifactId}`, token, {
    method: "PATCH",
    body: JSON.stringify(updates),
  });
}

export type ExportFormat = "json" | "markdown" | "csv";

export async function exportJob(
  token: string,
  jobId: string,
  format: ExportFormat,
): Promise<string> {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/export?format=${format}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!response.ok) {
    throw new Error(`Export failed: ${response.status}`);
  }
  return response.text();
}
