import { test, expect } from "@playwright/test";
import { login } from "./helpers";
import path from "path";
import fs from "fs";

test.describe("Knowledge Base", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("should show domain cards", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(page.getByRole("heading", { name: "Knowledge Base" })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("WELL Building Standard")).toBeVisible();
    await expect(page.getByText("Articles & Research")).toBeVisible();
    await expect(page.getByText("Product Recommendations")).toBeVisible();
  });

  test("should upload a text document", async ({ page }) => {
    // Create a temp test file
    const testFile = path.join(__dirname, "test-upload.txt");
    fs.writeFileSync(testFile, "This is a test document about wellness and biophilic design principles for healthy homes.");

    try {
      await page.goto("/knowledge/upload");
      await expect(page.getByText("Upload Document")).toBeVisible();

      // Fill form
      await page.locator("select").first().selectOption("research");
      await page.getByLabel("Title").fill("E2E Test Document");

      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(testFile);

      // Submit
      await page.getByRole("button", { name: "Upload and Ingest" }).click();

      // Should show success
      await expect(page.getByText(/chunks created/i)).toBeVisible({ timeout: 30000 });
    } finally {
      fs.unlinkSync(testFile);
    }
  });
});
