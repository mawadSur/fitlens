"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";
import { EmptyState, PageHeader, VisaBadge } from "@/components/ui";

const icons = {
  pin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0Z" /><circle cx="12" cy="10" r="3" /></svg>
  ),
  remote: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><circle cx="12" cy="12" r="2" /><path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14" /></svg>
  ),
  rate: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><line x1="12" y1="2" x2="12" y2="22" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
  ),
  source: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /></svg>
  ),
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  useEffect(() => {
    api.jobs().then(setJobs);
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Open Requirements"
        subtitle="Live roles sourced across the market, ready for matching."
      />

      {jobs.length === 0 ? (
        <EmptyState title="No open requirements" hint="New roles will appear here as they're sourced." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {jobs.map((j) => (
            <div key={j.id} className="card card-hover flex flex-col">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="font-display font-semibold tracking-tight text-ink">{j.title}</div>
                  <div className="mt-0.5 text-sm text-muted">{j.client}</div>
                </div>
                <span className="pill badge-muted shrink-0">
                  {icons.source}
                  {j.source}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-faint">
                <span className="inline-flex items-center gap-1.5">
                  {icons.pin}
                  <span className="text-slate-600">{j.location}</span>
                </span>
                {j.remote && (
                  <span className="inline-flex items-center gap-1.5 text-good">
                    {icons.remote}
                    Remote
                  </span>
                )}
              </div>

              {j.required_skills.length > 0 && (
                <div className="mt-4">
                  <div className="eyebrow mb-2">Required skills</div>
                  <div className="flex flex-wrap gap-1.5">
                    {j.required_skills.map((s) => (
                      <span key={s} className="pill badge-muted">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-4 flex items-end justify-between gap-3 border-t border-edge/70 pt-4">
                <div>
                  <div className="eyebrow">Rate band</div>
                  <div className="mt-0.5 inline-flex items-center gap-1.5 font-display text-lg font-semibold tabular-nums text-ink">
                    <span className="text-faint">{icons.rate}</span>
                    ${j.rate_band[0]}–{j.rate_band[1]}
                    <span className="text-sm font-normal text-faint">/hr</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="eyebrow mb-1.5">Work auth</div>
                  {j.visa_requirements.length ? (
                    <div className="flex flex-wrap justify-end gap-1.5">
                      {j.visa_requirements.map((v) => (
                        <VisaBadge key={v} visa={v} />
                      ))}
                    </div>
                  ) : (
                    <span className="pill badge-good">Any work auth</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
