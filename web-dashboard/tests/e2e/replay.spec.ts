import { expect, test } from "@playwright/test";

test("sample replay exposes final answer, tool call, and guardrail evidence", async ({ page }) => {
  await page.goto("/replay");

  await expect(page.getByText("Sample replay")).toBeVisible();
  await expect(page.getByRole("region", { name: "Final answer" }).getByText(/NullPointerException/)).toBeVisible();
  await expect(page.getByRole("region", { name: "Ordered tool calls" }).getByText("search_error_logs")).toBeVisible();
  const guardrail = page.getByRole("region", { name: "Guardrail review" });
  await expect(guardrail).toBeVisible();
  await expect(guardrail.locator("strong", { hasText: "SQL_WRITE_BLOCKED" })).toBeVisible();
});
