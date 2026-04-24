import { test, expect } from "@playwright/test";
import { login } from "./helpers";

test.describe("Products", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("should create a product", async ({ page }) => {
    await page.goto("/products");
    await page.getByRole("button", { name: "Add Product" }).click();

    await page.getByLabel("Name").fill("E2E Test Air Purifier");
    await page.getByLabel("Category").fill("air_quality");
    await page.locator("textarea").fill("Tested via Playwright");

    await page.getByRole("button", { name: "Save Product" }).click();

    await expect(page.getByText("E2E Test Air Purifier")).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Partners", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("should create a partner", async ({ page }) => {
    await page.goto("/partners");
    await page.getByRole("button", { name: "Add Partner" }).click();

    await page.getByLabel("Name", { exact: true }).fill("E2E Test Partner");
    await page.getByLabel("Category", { exact: true }).fill("organizer");
    await page.locator("textarea").fill("Tested via Playwright");

    await page.getByRole("button", { name: "Save Partner" }).click();

    await expect(page.getByText("E2E Test Partner")).toBeVisible({ timeout: 10000 });
  });
});
