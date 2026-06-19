"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type IconProps = { className?: string };

// Lucide-style stroke icons (consistent 1.75 stroke, 20px) — no emoji.
const Icon = {
  dashboard: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={p.className}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" />
    </svg>
  ),
  bench: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={p.className}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  jobs: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={p.className}>
      <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  ),
  submissions: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={p.className}>
      <path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" />
    </svg>
  ),
  integrations: (p: IconProps) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={p.className}>
      <path d="M9 2v6" /><path d="M15 2v6" /><path d="M9 8h6a4 4 0 0 1 4 4v0a4 4 0 0 1-4 4h-1" /><path d="M12 16v6" /><circle cx="12" cy="16" r="0.5" fill="currentColor" />
    </svg>
  ),
};

const links = [
  { href: "/", label: "Dashboard", icon: Icon.dashboard },
  { href: "/consultants", label: "Hot Bench", icon: Icon.bench },
  { href: "/jobs", label: "Jobs", icon: Icon.jobs },
  { href: "/submissions", label: "Submissions", icon: Icon.submissions },
  { href: "/integrations", label: "Integrations", icon: Icon.integrations },
];

export default function Nav() {
  const path = usePathname();
  return (
    <aside className="sticky top-0 flex h-dvh w-64 shrink-0 flex-col border-r border-edge bg-surface/80 px-4 py-6 backdrop-blur-xl">
      <Link href="/" className="flex items-center gap-3 px-2">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-soft text-white shadow-lift">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
            <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
          </svg>
        </span>
        <span className="leading-tight">
          <span className="block font-display text-lg font-semibold text-ink">FitLens</span>
          <span className="block text-[11px] font-medium text-muted">Workforce Intelligence</span>
        </span>
      </Link>

      <nav className="mt-8 flex flex-col gap-1">
        {links.map((l) => {
          const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
          const IconC = l.icon;
          return (
            <Link
              key={l.href}
              href={l.href}
              aria-current={active ? "page" : undefined}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-200 ${
                active
                  ? "bg-brand/10 text-brand-ink"
                  : "text-slate-500 hover:bg-slate-100 hover:text-ink"
              }`}
            >
              {active && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-brand" />}
              <IconC className={`h-5 w-5 transition-colors ${active ? "text-brand" : "text-faint group-hover:text-slate-600"}`} />
              {l.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-xl border border-edge bg-canvas/60 px-3 py-3 text-[11px] leading-relaxed text-muted">
        <div className="flex items-center gap-1.5 font-medium text-good">
          <span className="h-1.5 w-1.5 rounded-full bg-good" /> 12 agents live
        </div>
        <div className="mt-1 text-faint">Agentic BSOS · seeded demo data</div>
      </div>
    </aside>
  );
}
