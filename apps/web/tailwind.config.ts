import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b1020",
        panel: "#121a2e",
        edge: "#22304d",
        brand: { DEFAULT: "#5b8cff", soft: "#8fb0ff" },
        good: "#34d399",
        warn: "#fbbf24",
        bad: "#f87171",
      },
    },
  },
  plugins: [],
} satisfies Config;
