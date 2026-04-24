import { test, expect } from "@playwright/test";

test.describe("Authentication", () => {
  test("should show login page", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Sign in to your account")).toBeVisible({ timeout: 10000 });
  });

  test("should reject invalid credentials", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("wrong@example.com");
    await page.getByLabel("Password").fill("wrongpassword1");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByText(/Invalid|error/i)).toBeVisible({ timeout: 10000 });
  });

  test("should login and redirect to dashboard", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("practitioner@wellnessops.local");
    await page.getByLabel("Password").fill("wellness2026!");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });
  });

  test("should logout", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("practitioner@wellnessops.local");
    await page.getByLabel("Password").fill("wellness2026!");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({ timeout: 15000 });

    await page.getByText("Sign out").click();
    await expect(page.getByText("Sign in to your account")).toBeVisible({ timeout: 10000 });
  });
});
