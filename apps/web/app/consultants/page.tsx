"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Consultant } from "@/lib/types";
import { Money, VisaBadge } from "@/components/ui";

export default function ConsultantsPage() {
  const [rows, setRows] = useState<Consultant[]>([]);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.consultants().then(setRows).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="card text-bad">{err}</div>;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold text-white">Hot Bench</h1>
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase text-slate-500">
            <tr className="border-b border-edge">
              <th className="px-4 py-3">Consultant</th>
              <th>Visa</th>
              <th>Primary skill</th>
              <th>Status</th>
              <th>Availability</th>
              <th className="text-right">Rate</th>
              <th className="px-4 text-right">Bench cost/day</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id} className="border-b border-edge/40 hover:bg-edge/20">
                <td className="px-4 py-3">
                  <Link href={`/consultants/${c.id}`} className="font-medium text-brand-soft hover:underline">
                    {c.name}
                  </Link>
                  <div className="text-xs text-slate-500">{c.location}</div>
                </td>
                <td><VisaBadge visa={c.visa_status} /></td>
                <td className="text-slate-300">{c.primary_skill}</td>
                <td>
                  <span className="pill bg-edge text-slate-300">{c.status}</span>
                </td>
                <td className="text-slate-400">
                  {c.days_until_available != null
                    ? `in ${c.days_until_available}d`
                    : c.days_on_bench > 0
                    ? `${c.days_on_bench}d benched`
                    : "—"}
                </td>
                <td className="text-right tabular-nums text-slate-300">${c.expected_rate}/hr</td>
                <td className="px-4 text-right tabular-nums text-slate-400">
                  {c.daily_bench_cost ? <Money value={c.daily_bench_cost} /> : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
