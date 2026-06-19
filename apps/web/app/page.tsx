"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Dashboard } from "@/lib/types";
import { Money, Stat, VisaBadge } from "@/components/ui";

export default function DashboardPage() {
  const [d, setD] = useState<Dashboard | null>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    api.dashboard().then(setD).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="card text-bad">Failed to load: {err}</div>;
  if (!d) return <div className="text-slate-400">Loading dashboard…</div>;

  const rev = d.revenue_forecast;
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Recruiter Dashboard</h1>
        <p className="text-sm text-slate-400">Live view across the autonomous agent team.</p>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Consultants" value={d.counts.consultants} sub={`${d.counts.open_jobs} open jobs`} />
        <Stat label="On Hot Bench" value={d.hot_bench.length} sub="being marketed" />
        <Stat label="Bench Burn / mo" value={<Money value={d.total_daily_bench_cost * 30} />} sub={`$${d.total_daily_bench_cost}/day`} />
        <Stat label="Exp. Placements 30d" value={rev.expected_placements_30d} sub={<Money value={rev.expected_monthly_revenue} />} />
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="card lg:col-span-2">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Hot Bench</h2>
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="pb-2">Consultant</th>
                <th>Visa</th>
                <th>Skill</th>
                <th>Avail.</th>
                <th className="text-right">Bench cost</th>
              </tr>
            </thead>
            <tbody>
              {d.hot_bench.map((c: any) => (
                <tr key={c.consultant_id} className="border-t border-edge/60">
                  <td className="py-2 font-medium text-white">{c.name}</td>
                  <td><VisaBadge visa={c.visa_status} /></td>
                  <td className="text-slate-300">{c.primary_skill}</td>
                  <td className="text-slate-400">
                    {c.days_until_available != null ? `in ${c.days_until_available}d` : `${c.days_on_bench}d benched`}
                  </td>
                  <td className="text-right tabular-nums text-slate-300">
                    <Money value={c.bench_cost_accrued} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="space-y-6">
          <div className="card">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Revenue Forecast</h2>
            <dl className="space-y-2 text-sm">
              <Row k="Expected revenue / mo" v={<Money value={rev.expected_monthly_revenue} />} />
              <Row k="Gross margin" v={<Money value={rev.expected_gross_margin} />} />
              <Row k="Bench burn / mo" v={<span className="text-bad"><Money value={rev.bench_burn_monthly} /></span>} />
              <Row k="Consultants marketed" v={rev.consultants_marketed} />
            </dl>
          </div>

          <div className="card">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">Alerts</h2>
            <ul className="space-y-1.5 text-sm">
              {[...d.bench_alerts, ...d.immigration_alerts].slice(0, 6).map((a, i) => (
                <li key={i} className="flex gap-2 text-slate-300">
                  <span className="text-warn">▲</span> {a}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <section className="card">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
          Placement Prediction (top consultants)
        </h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {d.top_placements.map((p: any) => (
            <div key={p.consultant_id} className="rounded-lg border border-edge/60 p-3">
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{p.name}</span>
                <span className="text-lg font-semibold text-brand-soft">
                  {Math.round(p.placement_probability * 100)}%
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-400">{p.forecast}</div>
              <div className="mt-1 text-xs text-slate-500">best: {p.best_job ?? "—"}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-400">{k}</dt>
      <dd className="font-medium text-white">{v}</dd>
    </div>
  );
}
