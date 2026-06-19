"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Job } from "@/lib/types";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  useEffect(() => {
    api.jobs().then(setJobs);
  }, []);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-white">Open Requirements</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {jobs.map((j) => (
          <div key={j.id} className="card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-white">{j.title}</div>
                <div className="text-xs text-slate-400">{j.client} · {j.location}{j.remote ? " · Remote" : ""}</div>
              </div>
              <span className="pill bg-edge text-slate-300">{j.source}</span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {j.required_skills.map((s) => (
                <span key={s} className="pill bg-brand/10 text-brand-soft">{s}</span>
              ))}
            </div>
            <div className="mt-3 flex items-center justify-between text-sm">
              <span className="tabular-nums text-slate-300">${j.rate_band[0]}–{j.rate_band[1]}/hr</span>
              <span className="text-xs text-slate-500">
                {j.visa_requirements.length ? `Visa: ${j.visa_requirements.join(", ")}` : "Any work auth"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
