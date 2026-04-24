import { Page, expect } from "@playwright/test";

export async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Email").fill("practitioner@wellnessops.local");
  await page.getByLabel("Password").fill("wellness2026!");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });
}

export async function createClient(
  page: Page,
  name: string,
  options?: { budgetTier?: string; hasWearable?: boolean }
) {
  await page.goto("/clients/new");
  await page.getByLabel("Display Name").fill(name);

  if (options?.budgetTier) {
    const select = page.locator("select").first();
    await select.selectOption(options.budgetTier);
  }

  if (options?.hasWearable) {
    await page.getByLabel("Client has a wearable device").check();
  }

  await page.getByRole("button", { name: "Create Client" }).click();
  // Should redirect to client detail -- wait for audit buttons
  await expect(page.getByRole("button", { name: "Core Audit" })).toBeVisible({ timeout: 15000 });
}
