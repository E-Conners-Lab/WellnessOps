import { test, expect } from "@playwright/test";
import { login, createClient } from "./helpers";

test.describe("Free-Form Capture", () => {
  test("should categorize and save a free-form observation", async ({ page }) => {
    await login(page);
    await createClient(page, "Freeform Test Client");

    // Start audit
    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    // Go to free-form
    await page.getByRole("link", { name: "Free-Form Capture" }).click();
    await expect(page.getByText("Free-Form Capture")).toBeVisible({ timeout: 10000 });

    // Type observation
    await page.getByPlaceholder("Type or paste your observations").fill(
      "The fridge is mostly empty with just condiments and old takeout"
    );

    // Categorize
    await page.getByRole("button", { name: "Categorize" }).click();

    // Should show a result (may take a few seconds for Ollama)
    await expect(page.getByText(/Kitchen|kitchen/)).toBeVisible({ timeout: 30000 });

    // Save
    await page.getByRole("button", { name: /Save/ }).click();

    // Should show success
    await expect(page.getByText(/saved/i)).toBeVisible({ timeout: 5000 });
  });

  test("should split multi-room observations", async ({ page }) => {
    await login(page);
    await createClient(page, "Multi-Room Test");

    await page.getByRole("button", { name: "Core Audit" }).click();
    await expect(page.getByText("Overall Progress")).toBeVisible({ timeout: 10000 });

    await page.getByRole("link", { name: "Free-Form Capture" }).click();
    await expect(page.getByText("Free-Form Capture")).toBeVisible({ timeout: 10000 });

    // Multi-room observation
    await page.getByPlaceholder("Type or paste your observations").fill(
      "The fridge has only condiments and the nightstand is covered in work papers"
    );

    await page.getByRole("button", { name: "Categorize" }).click();

    // Should detect multiple areas
    await expect(
      page.getByText(/Detected \d+ observations|Kitchen|Bedroom/i)
    ).toBeVisible({ timeout: 30000 });
  });
});
