import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f6f7fb", // page background
        surface: "#ffffff", // cards
        ink: "#0f172a", // primary text / headings (slate-900)
        muted: "#64748b", // secondary text (slate-500)
        faint: "#94a3b8", // tertiary text (slate-400)
        edge: "#e7e9f1", // borders / dividers
        brand: {
          DEFAULT: "#4f46e5", // indigo-600
          soft: "#6366f1", // indigo-500
          ink: "#3730a3", // indigo-800 (text on tint)
          tint: "#eef2ff", // indigo-50
        },
        accent: { DEFAULT: "#f59e0b", ink: "#b45309", tint: "#fffbeb" },
        good: { DEFAULT: "#059669", soft: "#10b981", tint: "#ecfdf5" },
        warn: { DEFAULT: "#d97706", soft: "#f59e0b", tint: "#fffbeb" },
        bad: { DEFAULT: "#e11d48", soft: "#f43f5e", tint: "#fff1f2" },
      },
      fontFamily: {
        sans: ["var(--font-sans)", ...defaultTheme.fontFamily.sans],
        display: ["var(--font-display)", ...defaultTheme.fontFamily.sans],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgb(15 23 42 / 0.04), 0 4px 16px -4px rgb(15 23 42 / 0.08)",
        lift: "0 2px 4px 0 rgb(15 23 42 / 0.05), 0 12px 28px -8px rgb(79 70 229 / 0.18)",
      },
      borderRadius: { "2xl": "1rem", "3xl": "1.5rem" },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: { "fade-up": "fade-up 0.4s ease-out both" },
    },
  },
  plugins: [],
} satisfies Config;
