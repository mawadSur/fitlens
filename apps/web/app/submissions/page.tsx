"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Submission } from "@/lib/types";
import { ScoreBar } from "@/components/ui";

const statusColor: Record<string, string> = {
  submitted: "bg-brand/15 text-brand-soft",
  interview: "bg-warn/15 text-warn",
  placed: "bg-good/15 text-good",
  rejected: "bg-bad/15 text-bad",
  draft: "bg-edge text-slate-300",
};

export default function SubmissionsPage() {
  const [rows, setRows] = useState<Submission[]>([]);
  const reload = () => api.submissions().then(setRows);
  useEffect(() => {
    reload();
  }, []);

  async function schedule(id: number) {
    await api.scheduleInterview(id);
    reload();
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-white">Submissions</h1>
      {rows.length === 0 && (
        <div className="card text-slate-400" data-testid="no-submissions">
          No submissions yet — open a consultant and submit them to a matched job.
        </div>
      )}
      <div className="space-y-3" data-testid="submissions-list">
        {rows.map((s) => (
          <div key={s.id} className="card flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="font-medium text-white">
                {s.consultant_name} → {s.job_title}
              </div>
              <div className="text-xs text-slate-400">
                ${s.rate}/hr · submitted {s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "—"}
              </div>
            </div>
            <ScoreBar score={s.match_score} />
            <span className={`pill ${statusColor[s.status] ?? "bg-edge"}`}>{s.status}</span>
            {s.status === "submitted" && (
              <button className="btn-ghost" onClick={() => schedule(s.id)} data-testid={`schedule-${s.id}`}>
                Schedule interview
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
