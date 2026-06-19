import type { ReactNode } from "react";

export function VisaBadge({ visa }: { visa: string }) {
  const cls =
    visa === "USC" || visa === "GC" || visa === "GC_EAD"
      ? "badge-good"
      : visa === "H1B" || visa === "L1" || visa === "TN"
      ? "badge-brand"
      : "badge-warn";
  return <span className={`pill ${cls}`}>{visa}</span>;
}

const STATUS_STYLES: Record<string, string> = {
  available: "badge-good",
  placed: "badge-good",
  offer: "badge-good",
  marketing: "badge-brand",
  interview: "badge-brand",
  shortlisted: "badge-brand",
  submitted: "badge-muted",
  draft: "badge-muted",
  on_project: "badge-muted",
  rejected: "badge-bad",
  inactive: "badge-bad",
};

export function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_STYLES[status?.toLowerCase?.()] ?? "badge-muted";
  return <span className={`pill ${cls}`}>{status?.replace?.(/_/g, " ") ?? status}</span>;
}

export function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? "bg-good" : score >= 45 ? "bg-warn-soft" : "bg-bad";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-28 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
      <span className="tabular-nums text-sm font-semibold text-ink">{score.toFixed(0)}%</span>
    </div>
  );
}

export function Stat({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="card card-hover relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div className="eyebrow">{label}</div>
        {icon && (
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand/10 text-brand">{icon}</span>
        )}
      </div>
      <div className="stat-num mt-2">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions}
    </header>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card grid place-items-center py-12 text-center">
      <div className="text-sm font-medium text-ink">{title}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}

export function Money({ value }: { value: number }) {
  return <>${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}</>;
}
