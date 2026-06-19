"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Integration } from "@/lib/types";

export default function IntegrationsPage() {
  const [d, setD] = useState<Integration | null>(null);
  useEffect(() => {
    api.integrations().then(setD);
  }, []);
  if (!d) return <div className="text-slate-400">Loading…</div>;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-white">Integrations & Agents</h1>
      <div className="card">
        <div className="text-sm text-slate-300">
          Embedding backend: <span className="font-medium text-white">{d.embedder_backend}</span>
        </div>
        <div className="text-sm text-slate-400">
          {d.live_count} of {d.total} connectors live (the rest run in mock mode until credentials are supplied).
        </div>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {d.connectors.map((c) => (
          <div key={c.name} className="card">
            <div className="flex items-center justify-between">
              <span className="font-medium capitalize text-white">{c.name}</span>
              <span className={`pill ${c.live ? "bg-good/15 text-good" : "bg-warn/15 text-warn"}`}>
                {c.live ? "LIVE" : "MOCK"}
              </span>
            </div>
            <div className="mt-1 text-xs text-slate-500">{c.category}</div>
            {c.note && <div className="mt-2 text-xs text-slate-400">{c.note}</div>}
            {c.missing_credentials.length > 0 && (
              <div className="mt-2 text-[11px] text-slate-500">
                Needs: {c.missing_credentials.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
