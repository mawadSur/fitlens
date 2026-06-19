"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Consultant } from "@/lib/types";
import { EmptyState, Money, PageHeader, StatusBadge, VisaBadge } from "@/components/ui";

export default function ConsultantsPage() {
  const [rows, setRows] = useState<Consultant[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.consultants().then(setRows).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="card border-bad/30 text-bad">{err}</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hot Bench"
        subtitle="Consultants being marketed across the autonomous agent team."
      />

      {rows.length === 0 ? (
        <EmptyState title="No consultants on the bench" hint="Newly added consultants will appear here." />
      ) : (
        <div className="card p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="eyebrow text-left">
                <tr>
                  <th className="px-5 pb-2 pt-4 font-semibold">Consultant</th>
                  <th className="font-semibold">Visa</th>
                  <th className="font-semibold">Primary skill</th>
                  <th className="font-semibold">Status</th>
                  <th className="font-semibold">Availability</th>
                  <th className="text-right font-semibold">Rate</th>
                  <th className="px-5 text-right font-semibold">Bench cost/day</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.id} className="table-row">
                    <td className="px-5 py-3">
                      <Link
                        href={`/consultants/${c.id}`}
                        className="font-medium text-brand hover:underline"
                      >
                        {c.name}
                      </Link>
                      <div className="text-xs text-faint">{c.location}</div>
                    </td>
                    <td><VisaBadge visa={c.visa_status} /></td>
                    <td className="text-slate-600">{c.primary_skill}</td>
                    <td><StatusBadge status={c.status} /></td>
                    <td className="text-muted">
                      {c.days_until_available != null
                        ? `in ${c.days_until_available}d`
                        : c.days_on_bench > 0
                        ? `${c.days_on_bench}d benched`
                        : "—"}
                    </td>
                    <td className="text-right tabular-nums font-medium text-slate-700">${c.expected_rate}/hr</td>
                    <td className="px-5 text-right tabular-nums text-muted">
                      {c.daily_bench_cost ? <Money value={c.daily_bench_cost} /> : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
