import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "FitLens — Workforce Supply Intelligence",
  description: "Agentic Bench Sales Operating System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen">
          <Nav />
          <main className="flex-1 overflow-x-hidden px-8 py-7">{children}</main>
        </div>
      </body>
    </html>
  );
}
