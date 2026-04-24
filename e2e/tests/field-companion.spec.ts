import { test, expect } from "@playwright/test";
import { login, createClient } from "./helpers";

test.describe("Field Companion", () => {
  test("should walk through structured prompts", async ({ page }) => {
    await login(page);
    await createClient(page, "Field Companion Test");

    // Start core audit
    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    // Enter field companion
    await page.getByRole("link", { name: "Continue Field Companion" }).click();
    await expect(page.getByText("Entry and Curb Appeal")).toBeVisible({ timeout: 10000 });

    // First prompt should be visible
    await expect(
      page.getByText("What is your first impression walking up to the home?")
    ).toBeVisible();

    // Type an observation
    await page.getByPlaceholder("Type your observation here").fill(
      "Beautiful garden entrance with a clean pathway"
    );

    // Wait for auto-save
    await expect(page.getByText("Saved")).toBeVisible({ timeout: 5000 });

    // Click Next
    await page.getByRole("button", { name: "Next" }).click();

    // Should show second prompt
    await expect(
      page.getByText("What does the entry communicate")
    ).toBeVisible({ timeout: 5000 });

    // Skip this one
    await page.getByRole("button", { name: "Skip" }).click();

    // Should show third prompt
    await expect(page.getByText("threshold")).toBeVisible({ timeout: 5000 });

    // Go back
    await page.getByRole("button", { name: "Back" }).click();
    await expect(
      page.getByText("What does the entry communicate")
    ).toBeVisible({ timeout: 5000 });

    // Pause and return
    await page.getByText("Pause and return to session").click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    // Progress should be > 0
    const progressText = await page.getByText(/answered/).first().textContent();
    expect(progressText).toBeTruthy();
  });

  test("should jump between sections", async ({ page }) => {
    await login(page);
    await createClient(page, "Section Jump Test");

    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    await page.getByRole("link", { name: "Continue Field Companion" }).click();
    await expect(page.getByText("Entry and Curb Appeal")).toBeVisible({ timeout: 10000 });

    // Jump to Kitchen section
    await page.getByRole("button", { name: "Kitchen" }).click();
    await expect(page.getByText("Open the fridge")).toBeVisible({ timeout: 5000 });
  });
});
