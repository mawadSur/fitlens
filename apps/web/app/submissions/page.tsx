"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Submission } from "@/lib/types";
import { EmptyState, PageHeader, ScoreBar, StatusBadge } from "@/components/ui";

const icons = {
  calendar: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
  ),
  arrow: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4 text-faint"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
  ),
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
    <div className="space-y-6">
      <PageHeader
        title="Submissions"
        subtitle="Consultants submitted to matched roles, tracked through interview."
      />

      {rows.length === 0 && (
        <div data-testid="no-submissions">
          <EmptyState
            title="No submissions yet"
            hint="Open a consultant and submit them to a matched job to see it here."
          />
        </div>
      )}

      <div className="space-y-3" data-testid="submissions-list">
        {rows.map((s) => (
          <div key={s.id} className="card card-hover flex flex-wrap items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 font-medium text-ink">
                <span className="truncate">{s.consultant_name}</span>
                {icons.arrow}
                <span className="truncate text-slate-600">{s.job_title}</span>
              </div>
              <div className="mt-0.5 text-xs text-faint">
                ${s.rate}/hr · submitted {s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "—"}
              </div>
            </div>
            <ScoreBar score={s.match_score} />
            <StatusBadge status={s.status} />
            {s.status === "submitted" && (
              <button className="btn-ghost" onClick={() => schedule(s.id)} data-testid={`schedule-${s.id}`}>
                {icons.calendar}
                Schedule interview
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
