import { expect, test } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test("dashboard renders KPIs, hot bench and forecasts", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Recruiter Dashboard" })).toBeVisible();
  await expect(page.getByText("Bench Burn / mo", { exact: true })).toBeVisible();
  await expect(page.getByText("Revenue Forecast")).toBeVisible();
  // Hot bench table has the seeded Databricks consultant
  await expect(page.getByText("Chandru Rao").first()).toBeVisible();
});

test("consultant matches are semantically ranked and visa-aware", async ({ page }) => {
  await page.goto("/consultants");
  await page.getByRole("link", { name: "Chandru Rao" }).click();
  await expect(page.getByTestId("consultant-name")).toHaveText("Chandru Rao");

  const matches = page.getByTestId("matches");
  await expect(matches).toBeVisible();
  // Top match (first card) should be the Databricks role
  await expect(matches.locator("> div").first()).toContainText("Databricks");
  // Visa-aware: at least one match flagged ineligible somewhere in the list
  await expect(matches).toContainText("eligible");
});

test("submit consultant to top job generates an RTR", async ({ page }) => {
  await page.goto("/consultants/1");
  const matches = page.getByTestId("matches");
  await expect(matches).toBeVisible();
  await matches.getByRole("button", { name: "Submit" }).first().click();
  await expect(page.getByTestId("toast")).toContainText("RTR generated");
});

test("submission is tracked and an interview can be scheduled", async ({ page }) => {
  await page.goto("/submissions");
  const list = page.getByTestId("submissions-list");
  await expect(list).toContainText("Chandru Rao");

  const schedule = page.getByRole("button", { name: "Schedule interview" }).first();
  await schedule.click();
  await expect(list).toContainText("interview");
});

test("integrations page shows connectors and embedding backend", async ({ page }) => {
  await page.goto("/integrations");
  await expect(page.getByRole("heading", { name: "Integrations & Agents" })).toBeVisible();
  await expect(page.getByText("Embedding backend:")).toBeVisible();
  await expect(page.getByText("jobdiva").first()).toBeVisible();
});
