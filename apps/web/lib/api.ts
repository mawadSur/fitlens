// Same-origin: Next rewrites /api/* to the FastAPI backend (see next.config.mjs).
async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { cache: "no-store", ...init });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} on ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () => req<import("./types").Dashboard>("/api/dashboard"),
  consultants: () => req<import("./types").Consultant[]>("/api/consultants"),
  consultant: (id: number) => req<import("./types").Consultant>(`/api/consultants/${id}`),
  matches: (id: number) =>
    req<{ matches: import("./types").Match[] }>(`/api/consultants/${id}/matches?top_k=5`),
  jobs: () => req<import("./types").Job[]>("/api/jobs"),
  submissions: () => req<import("./types").Submission[]>("/api/submissions"),
  integrations: () => req<import("./types").Integration>("/api/integrations"),
  createSubmission: (body: { consultant_id: number; job_id: number; rate?: number }) =>
    req<any>("/api/submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  scheduleInterview: (submissionId: number) =>
    req<any>(`/api/submissions/${submissionId}/interview`, { method: "POST" }),
  uploadResume: (consultantId: number, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<any>(`/api/consultants/${consultantId}/resume`, { method: "POST", body: fd });
  },
};
