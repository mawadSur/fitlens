import { defineConfig } from "@playwright/test";

// Uses the system-installed Google Chrome (channel: "chrome") so we don't
// download a separate Chromium (saves disk). Servers are started separately.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3000",
    channel: "chrome",
    headless: true,
    screenshot: "only-on-failure",
  },
});
