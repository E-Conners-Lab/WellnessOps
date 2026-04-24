import { test, expect } from "@playwright/test";
import { login, createClient } from "./helpers";

test.describe("Client Management", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("should show client list page", async ({ page }) => {
    await page.goto("/clients");
    await expect(page.getByRole("heading", { name: "Clients" })).toBeVisible({ timeout: 10000 });
  });

  test("should create a new client", async ({ page }) => {
    const name = `E2E Client ${Date.now()}`;
    await createClient(page, name, { budgetTier: "moderate" });
    await expect(page.getByText(name)).toBeVisible();
    await expect(page.getByRole("button", { name: "Core Audit" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Extended Audit" })).toBeVisible();
  });

  test("should show created client in list", async ({ page }) => {
    const name = `List Client ${Date.now()}`;
    await createClient(page, name);
    await page.goto("/clients");
    await expect(page.getByText(name)).toBeVisible({ timeout: 10000 });
  });

  test("should start a core audit from client detail", async ({ page }) => {
    const name = `Audit Client ${Date.now()}`;
    await createClient(page, name);
    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });
  });
});
