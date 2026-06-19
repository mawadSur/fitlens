"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { Money, PageHeader, Stat, VisaBadge } from "@/components/ui";

const icons = {
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /></svg>
  ),
  flame: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5Z" /></svg>
  ),
  burn: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><line x1="12" y1="2" x2="12" y2="22" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
  ),
  trend: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4"><path d="M3 17l6-6 4 4 8-8" /><path d="M17 7h4v4" /></svg>
  ),
};

export default function DashboardPage() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    api.dashboard().then(setD).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="card border-bad/30 text-bad">Failed to load: {err}</div>;
  if (!d) return <div className="text-muted">Loading dashboard…</div>;

  const rev = d.revenue_forecast;
  return (
    <div className="space-y-6">
      <PageHeader
        title="Recruiter Dashboard"
        subtitle="Live view across the autonomous agent team."
      />

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Consultants" value={d.counts.consultants} sub={`${d.counts.open_jobs} open jobs`} icon={icons.users} />
        <Stat label="On Hot Bench" value={d.hot_bench.length} sub="being marketed" icon={icons.flame} />
        <Stat label="Bench Burn / mo" value={<Money value={d.total_daily_bench_cost * 30} />} sub={`$${d.total_daily_bench_cost}/day`} icon={icons.burn} />
        <Stat label="Exp. Placements 30d" value={rev.expected_placements_30d} sub={<Money value={rev.expected_monthly_revenue} />} icon={icons.trend} />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="card lg:col-span-2">
          <h2 className="eyebrow mb-3">Hot Bench</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="eyebrow text-left">
                <tr>
                  <th className="pb-2 font-semibold">Consultant</th>
                  <th className="font-semibold">Visa</th>
                  <th className="font-semibold">Skill</th>
                  <th className="font-semibold">Avail.</th>
                  <th className="text-right font-semibold">Bench cost</th>
                </tr>
              </thead>
              <tbody>
                {d.hot_bench.map((c: any) => (
                  <tr key={c.consultant_id} className="table-row">
                    <td className="py-2.5 font-medium text-ink">{c.name}</td>
                    <td><VisaBadge visa={c.visa_status} /></td>
                    <td className="text-slate-600">{c.primary_skill}</td>
                    <td className="text-muted">
                      {c.days_until_available != null ? `in ${c.days_until_available}d` : `${c.days_on_bench}d benched`}
                    </td>
                    <td className="text-right tabular-nums font-medium text-slate-700">
                      <Money value={c.bench_cost_accrued} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-6">
          <div className="card">
            <h2 className="eyebrow mb-3">Revenue Forecast</h2>
            <dl className="space-y-2.5 text-sm">
              <Row k="Expected revenue / mo" v={<Money value={rev.expected_monthly_revenue} />} />
              <Row k="Gross margin" v={<Money value={rev.expected_gross_margin} />} />
              <Row k="Bench burn / mo" v={<span className="text-bad"><Money value={rev.bench_burn_monthly} /></span>} />
              <Row k="Consultants marketed" v={rev.consultants_marketed} />
            </dl>
          </div>

          <div className="card">
            <h2 className="eyebrow mb-3">Alerts</h2>
            <ul className="space-y-2 text-sm">
              {[...d.bench_alerts, ...d.immigration_alerts].slice(0, 6).map((a, i) => (
                <li key={i} className="flex gap-2.5 text-slate-600">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-md bg-warn/10 text-warn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-3 w-3"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                  </span>
                  {a}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <section className="card">
        <h2 className="eyebrow mb-3">Placement Prediction (top consultants)</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {d.top_placements.map((p: any) => (
            <div key={p.consultant_id} className="card-hover rounded-xl border border-edge bg-canvas/40 p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink">{p.name}</span>
                <span className="font-display text-lg font-semibold tabular-nums text-brand">
                  {Math.round(p.placement_probability * 100)}%
                </span>
              </div>
              <div className="mt-1.5 text-xs text-slate-600">{p.forecast}</div>
              <div className="mt-0.5 text-xs text-faint">best: {p.best_job ?? "—"}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-muted">{k}</dt>
      <dd className="font-medium tabular-nums text-ink">{v}</dd>
    </div>
  );
}
