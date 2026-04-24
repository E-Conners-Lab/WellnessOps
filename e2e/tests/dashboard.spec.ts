import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test.describe("Dashboard", () => {
  test("should show dashboard stats after login", async ({ page }) => {
    await login(page);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    // Wait for API data to load
    await expect(page.getByText("Scoring Calibration")).toBeVisible({ timeout: 10000 });
  });

  test("should navigate to all main sections", async ({ page }) => {
    await login(page);

    // Clients
    await page.getByRole("link", { name: "Clients" }).first().click();
    await expect(page.getByRole("heading", { name: "Clients" })).toBeVisible({ timeout: 10000 });

    // Knowledge Base
    await page.getByRole("link", { name: "Knowledge Base" }).first().click();
    await expect(page.getByRole("heading", { name: "Knowledge Base" })).toBeVisible({ timeout: 10000 });

    // Products
    await page.getByRole("link", { name: "Products" }).first().click();
    await expect(page.getByRole("heading", { name: "Products" })).toBeVisible({ timeout: 10000 });

    // Partners
    await page.getByRole("link", { name: "Partners" }).first().click();
    await expect(page.getByRole("heading", { name: "Partners" })).toBeVisible({ timeout: 10000 });

    // Back to Dashboard
    await page.getByRole("link", { name: "Dashboard" }).first().click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 10000 });
  });
});
