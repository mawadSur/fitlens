export function VisaBadge({ visa }: { visa: string }) {
  const cls =
    visa === "USC" || visa === "GC" || visa === "GC_EAD"
      ? "bg-good/15 text-good"
      : visa === "H1B" || visa === "L1" || visa === "TN"
      ? "bg-brand/15 text-brand-soft"
      : "bg-warn/15 text-warn";
  return <span className={`pill ${cls}`}>{visa}</span>;
}

export function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? "bg-good" : score >= 45 ? "bg-warn" : "bg-bad";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-28 overflow-hidden rounded-full bg-edge">
        <div className={`h-full ${color}`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
      <span className="tabular-nums text-sm font-semibold text-white">{score.toFixed(0)}%</span>
    </div>
  );
}

export function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="stat-num mt-1">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-400">{sub}</div>}
    </div>
  );
}

export function Money({ value }: { value: number }) {
  return <>${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</>;
}
