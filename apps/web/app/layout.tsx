import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import Nav from "@/components/Nav";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const display = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "FitLens — Workforce Supply Intelligence",
  description: "Agentic Bench Sales Operating System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${display.variable}`}>
      <body>
        <div className="flex min-h-dvh">
          <Nav />
          <main className="flex-1 overflow-x-hidden px-5 py-6 sm:px-8 sm:py-8">
            <div className="mx-auto w-full max-w-7xl animate-fade-up">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
