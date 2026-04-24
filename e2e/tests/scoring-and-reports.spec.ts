import { test, expect } from "@playwright/test";
import { login, createClient } from "./helpers";

test.describe("Scoring and Reports", () => {
  test("full audit flow: observations -> scores -> report -> PDF", async ({ page }) => {
    await login(page);
    await createClient(page, "Full Flow Test");

    // Start core audit
    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    // Add some observations via field companion
    await page.getByRole("link", { name: "Continue Field Companion" }).click();
    await expect(page.getByText("Entry and Curb Appeal")).toBeVisible({ timeout: 10000 });

    // Fill first 3 prompts
    for (const observation of [
      "Clean entrance with a welcome mat",
      "Warm and inviting entry",
      "Good transition from outside to inside",
    ]) {
      await page.getByPlaceholder("Type your observation here").fill(observation);
      await expect(page.getByText("Saved")).toBeVisible({ timeout: 5000 });
      await page.getByRole("button", { name: "Next" }).click();
      await page.waitForTimeout(500);
    }

    // Skip the rest and go back to session
    await page.getByText("Pause and return to session").click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    // Finish observations
    await page.getByRole("button", { name: "Finish Observations" }).click();
    await expect(page.getByText("observations complete")).toBeVisible({ timeout: 5000 });

    // Generate scores
    await page.getByRole("link", { name: "Generate Scores" }).click();
    await expect(page.getByText("Score Review")).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /Generate Scores/ }).click();

    // Wait for scores to generate (Ollama takes 30-60 seconds)
    await expect(page.getByText(/Generating scores/)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/\/10/)).toBeVisible({ timeout: 120000 });

    // Verify overall score appears
    await expect(page.getByText(/out of 100/)).toBeVisible();

    // Override a score
    const firstOverrideBtn = page.getByText("Override").first();
    await firstOverrideBtn.click();
    await page.getByRole("button", { name: "Save Override" }).click();

    // Generate report
    await page.getByRole("link", { name: "Generate Report" }).click();

    // Wait for report generation
    await expect(page.getByText("Client Report")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/out of 100/)).toBeVisible({ timeout: 120000 });

    // Verify report sections
    await expect(page.getByText("Category Scores")).toBeVisible();
    await expect(page.getByText("Priority Action Plan")).toBeVisible();
    await expect(page.getByText("What Changes When You Fix This")).toBeVisible();
    await expect(page.getByText("Next Steps")).toBeVisible();

    // Approve report
    await page.getByRole("button", { name: "Approve and Generate PDF" }).click();
    await expect(page.getByText("finalized")).toBeVisible({ timeout: 30000 });

    // PDF download button should appear
    await expect(page.getByRole("button", { name: "Download PDF" })).toBeVisible();
  });
});
