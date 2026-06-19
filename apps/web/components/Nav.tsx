"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard", icon: "▣" },
  { href: "/consultants", label: "Hot Bench", icon: "◑" },
  { href: "/jobs", label: "Jobs", icon: "▤" },
  { href: "/submissions", label: "Submissions", icon: "➦" },
  { href: "/integrations", label: "Integrations", icon: "⇄" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-edge bg-panel/60 px-4 py-6">
      <div className="px-2">
        <div className="text-lg font-semibold text-white">FitLens</div>
        <div className="text-xs text-brand-soft">Workforce Supply Intelligence</div>
      </div>
      <nav className="mt-8 flex flex-col gap-1">
        {links.map((l) => {
          const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                active ? "bg-brand/15 text-white" : "text-slate-400 hover:bg-edge/40 hover:text-slate-200"
              }`}
            >
              <span className="text-brand-soft">{l.icon}</span>
              {l.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-2 text-[11px] leading-relaxed text-slate-500">
        Agentic BSOS · 12 agents
        <br />
        Dev build — seeded data
      </div>
    </aside>
  );
}
