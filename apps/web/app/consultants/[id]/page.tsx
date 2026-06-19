"use client";

import { use, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Consultant, Match } from "@/lib/types";
import { EmptyState, Money, ScoreBar, Stat, VisaBadge } from "@/components/ui";

const icons = {
  upload: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
  ),
  briefcase: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" /></svg>
  ),
  user: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
  ),
  stamp: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M5 22h14" /><path d="M19.27 13.73A2.5 2.5 0 0 0 17.5 13h-11A2.5 2.5 0 0 0 4 15.5V17a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-1.5a2.5 2.5 0 0 0-.73-1.77Z" /><path d="M14 13V8.5C14 7 15 7 15 5a3 3 0 0 0-3-3 3 3 0 0 0-3 3c0 2 1 2 1 3.5V13" /></svg>
  ),
  check: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M20 6 9 17l-5-5" /></svg>
  ),
  send: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" /></svg>
  ),
  spark: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M12 3v3m0 12v3m9-9h-3M6 12H3m13.5-5.5-2 2m-7 7-2 2m11 0-2-2m-7-7-2-2" /></svg>
  ),
};

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

  if (!c) return <div className="text-muted">Loading…</div>;

  return (
    <div className="space-y-6">
      {toast && (
        <div
          data-testid="toast"
          className="card flex items-center gap-2.5 border-good/40 bg-good/10 text-sm font-medium text-good"
        >
          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-good/15">{icons.check}</span>
          {toast}
        </div>
      )}

      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink" data-testid="consultant-name">{c.name}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
            <VisaBadge visa={c.visa_status} />
            <span className="text-slate-700">{c.primary_skill}</span>
            <span className="text-faint">·</span>
            <span>{c.years_experience}y</span>
            <span className="text-faint">·</span>
            <span className="tabular-nums">${c.expected_rate}/hr</span>
            <span className="text-faint">·</span>
            <span>{c.location}</span>
          </div>
        </div>
        <div>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" hidden onChange={onUpload} data-testid="resume-input" />
          <button className="btn-ghost" onClick={() => fileRef.current?.click()} data-testid="upload-resume">
            {icons.upload}
            Upload résumé
          </button>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Years Experience" value={`${c.years_experience}y`} sub={c.primary_skill} icon={icons.user} />
        <Stat label="Expected Rate" value={<Money value={c.expected_rate} />} sub="per hour" icon={icons.briefcase} />
        <Stat
          label="Bench"
          value={c.days_until_available != null ? `${c.days_until_available}d` : `${c.days_on_bench}d`}
          sub={c.days_until_available != null ? "until available" : "on bench"}
          icon={icons.stamp}
        />
        <Stat label="Job Matches" value={matches.length} sub="AI-ranked" icon={icons.spark} />
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card lg:col-span-1">
          <h2 className="eyebrow mb-3">Profile</h2>
          <div className="flex flex-wrap gap-1.5">
            {c.skills.map((s) => (
              <span key={s} className="badge-muted pill">{s}</span>
            ))}
          </div>
          {c.immigration && (
            <div className="mt-4 border-t border-edge pt-4 text-sm">
              <div className="eyebrow mb-2">Immigration</div>
              <dl className="space-y-1.5">
                <ImmRow k="Visa" v={String((c.immigration as any).visa_type)} />
                <ImmRow k="Worksite" v={String((c.immigration as any).worksite_location || "—")} />
                <ImmRow k="EAD expiry" v={String((c.immigration as any).ead_expiry || "—")} />
              </dl>
            </div>
          )}
        </div>

        <div className="card lg:col-span-2">
          <h2 className="eyebrow mb-3">AI Job Matches</h2>
          <div className="space-y-3" data-testid="matches">
            {matches.length === 0 ? (
              <EmptyState title="No job matches yet" hint="Upload a résumé to surface AI-ranked openings." />
            ) : (
              matches.map((m) => (
                <div key={m.job_id} className="card-hover rounded-xl border border-edge bg-canvas/40 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 font-medium text-ink">
                        <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md bg-brand/10 text-brand">{icons.briefcase}</span>
                        {m.title}
                      </div>
                      <div className="mt-1 text-xs text-muted">
                        {m.client} · {m.location} · <span className="tabular-nums">${m.rate_band[0]}–{m.rate_band[1]}/hr</span> · via {m.source}
                      </div>
                    </div>
                    <ScoreBar score={m.match_score} />
                  </div>

                  <div className="mt-3 flex flex-wrap items-center gap-1.5">
                    <span className="badge-muted pill tabular-nums">skill {Math.round(m.skill_overlap * 100)}%</span>
                    <span className="badge-muted pill tabular-nums">rate-fit {Math.round(m.rate_fit * 100)}%</span>
                    <span className={`pill tabular-nums ${m.visa_eligible ? "badge-good" : "badge-bad"}`}>
                      visa {m.visa_eligible ? "eligible" : "ineligible"}
                    </span>
                    <span className="badge-muted pill tabular-nums">interview {Math.round(m.interview_probability * 100)}%</span>
                    <span className="badge-muted pill tabular-nums">placement {Math.round(m.placement_probability * 100)}%</span>
                    <button
                      className="btn ml-auto"
                      disabled={busy === m.job_id}
                      onClick={() => submit(m.job_id)}
                      data-testid={`submit-${m.job_id}`}
                    >
                      {busy === m.job_id ? (
                        "Submitting…"
                      ) : (
                        <>
                          {icons.send}
                          Submit
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function ImmRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted">{k}</dt>
      <dd className="font-medium text-slate-700">{v}</dd>
    </div>
  );
}
