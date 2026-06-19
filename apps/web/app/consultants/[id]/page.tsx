"use client";

import { use, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Consultant, Match } from "@/lib/types";
import { Money, ScoreBar, VisaBadge } from "@/components/ui";

export default function ConsultantDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const cid = Number(id);
  const [c, setC] = useState<Consultant | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [toast, setToast] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    api.consultant(cid).then(setC);
    api.matches(cid).then((r) => setMatches(r.matches));
  };
  useEffect(load, [cid]);

  const flash = (m: string) => {
    setToast(m);
    setTimeout(() => setToast(""), 4000);
  };

  async function submit(jobId: number) {
    setBusy(jobId);
    try {
      const r = await api.createSubmission({ consultant_id: cid, job_id: jobId });
      flash(`Submitted to job #${r.job_id} at $${r.rate}/hr — RTR generated (match ${r.match_score}%).`);
    } catch (e) {
      flash(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const r = await api.uploadResume(cid, file);
      flash(`Parsed ${r.parsed_skills.length} skills from ${r.filename}.`);
      load();
    } catch (err) {
      flash(String(err));
    }
  }

  if (!c) return <div className="text-slate-400">Loading…</div>;

  return (
    <div className="space-y-6">
      {toast && (
        <div data-testid="toast" className="card border-good/40 bg-good/10 text-sm text-good">
          {toast}
        </div>
      )}

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white" data-testid="consultant-name">{c.name}</h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-slate-400">
            <VisaBadge visa={c.visa_status} />
            <span>{c.primary_skill}</span>
            <span>· {c.years_experience}y</span>
            <span>· ${c.expected_rate}/hr</span>
            <span>· {c.location}</span>
          </div>
        </div>
        <div>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={onUpload} data-testid="resume-input" />
          <button className="btn-ghost" onClick={() => fileRef.current?.click()} data-testid="upload-resume">
            ⤴ Upload résumé
          </button>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-1">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Profile</h2>
          <div className="flex flex-wrap gap-1.5">
            {c.skills.map((s) => (
              <span key={s} className="pill bg-edge text-slate-300">{s}</span>
            ))}
          </div>
          {c.immigration && (
            <div className="mt-4 border-t border-edge/60 pt-3 text-sm">
              <div className="text-xs uppercase text-slate-500">Immigration</div>
              <div className="mt-1 text-slate-300">Visa: {String((c.immigration as any).visa_type)}</div>
              <div className="text-slate-400">Worksite: {String((c.immigration as any).worksite_location || "—")}</div>
              <div className="text-slate-400">EAD expiry: {String((c.immigration as any).ead_expiry || "—")}</div>
            </div>
          )}
        </div>

        <div className="card lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            AI Job Matches
          </h2>
          <div className="space-y-3" data-testid="matches">
            {matches.map((m) => (
              <div key={m.job_id} className="rounded-lg border border-edge/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-medium text-white">{m.title}</div>
                    <div className="text-xs text-slate-400">
                      {m.client} · {m.location} · ${m.rate_band[0]}–{m.rate_band[1]}/hr · via {m.source}
                    </div>
                  </div>
                  <ScoreBar score={m.match_score} />
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-slate-400">
                  <span>skill {Math.round(m.skill_overlap * 100)}%</span>
                  <span>rate-fit {Math.round(m.rate_fit * 100)}%</span>
                  <span className={m.visa_eligible ? "text-good" : "text-bad"}>
                    visa {m.visa_eligible ? "eligible" : "ineligible"}
                  </span>
                  <span>interview {Math.round(m.interview_probability * 100)}%</span>
                  <span>placement {Math.round(m.placement_probability * 100)}%</span>
                  <button
                    className="btn ml-auto"
                    disabled={busy === m.job_id}
                    onClick={() => submit(m.job_id)}
                    data-testid={`submit-${m.job_id}`}
                  >
                    {busy === m.job_id ? "Submitting…" : "Submit"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
