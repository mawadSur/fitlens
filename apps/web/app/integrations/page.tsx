"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Integration } from "@/lib/types";
import { PageHeader, Stat } from "@/components/ui";

const icons = {
  plug: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M9 2v6" /><path d="M15 2v6" /><path d="M6 8h12v3a6 6 0 0 1-12 0V8Z" /><path d="M12 17v5" /></svg>
  ),
  live: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
  ),
  cpu: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><path d="M9 2v2" /><path d="M15 2v2" /><path d="M9 20v2" /><path d="M15 20v2" /><path d="M20 9h2" /><path d="M20 15h2" /><path d="M2 9h2" /><path d="M2 15h2" /></svg>
  ),
  check: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><path d="M20 6 9 17l-5-5" /></svg>
  ),
  flask: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5"><path d="M9 3h6" /><path d="M10 3v6.5L5 18a2 2 0 0 0 1.7 3h10.6A2 2 0 0 0 19 18l-5-8.5V3" /><path d="M7.5 14h9" /></svg>
  ),
};

export default function IntegrationsPage() {
  const [d, setD] = useState<Integration | null>(null);
  useEffect(() => {
    api.integrations().then(setD);
  }, []);
  if (!d) return <div className="text-muted">Loading integrations…</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Integrations & Agents"
        subtitle="Connectors powering the autonomous agent team."
      />

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <Stat label="Live Connectors" value={d.live_count} sub={`of ${d.total} configured`} icon={icons.live} />
        <Stat label="Total Connectors" value={d.total} sub="across all categories" icon={icons.plug} />
        <div className="card card-hover relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div className="eyebrow">Embedding</div>
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand/10 text-brand">{icons.cpu}</span>
          </div>
          <div className="mt-2 text-sm text-slate-600">
            Embedding backend:{" "}
            <span className="font-display text-base font-semibold capitalize text-ink">{d.embedder_backend}</span>
          </div>
        </div>
      </section>

      <div className="card">
        <p className="text-sm text-slate-600">
          <span className="font-medium text-ink">{d.live_count}</span> of{" "}
          <span className="font-medium text-ink">{d.total}</span> connectors live — the rest run in mock mode until
          credentials are supplied.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="eyebrow">Connectors</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {d.connectors.map((c) => (
            <div key={c.name} className="card card-hover">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium capitalize text-ink">{c.name}</div>
                  <div className="mt-0.5 text-xs text-faint capitalize">{c.category}</div>
                </div>
                <span className={`pill ${c.live ? "badge-good" : "badge-muted"}`}>
                  {c.live ? icons.check : icons.flask}
                  {c.live ? "LIVE" : "MOCK"}
                </span>
              </div>
              {c.note && <div className="mt-3 text-xs text-muted">{c.note}</div>}
              {c.missing_credentials.length > 0 && (
                <div className="mt-2 text-[11px] text-faint">
                  Needs: {c.missing_credentials.join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
