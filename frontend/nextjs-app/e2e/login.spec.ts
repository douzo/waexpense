import { test, expect } from "@playwright/test";

test("login flow requests code and verifies", async ({ page }) => {
  await page.route("**/auth/request-code", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/auth/verify-code", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-access",
        refresh_token: "test-refresh",
        expires_in: 900,
        token_type: "bearer",
      }),
    });
  });

  await page.route("**/api/expenses**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.route("**/api/profile", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "u1",
        whatsapp_id: "wa1",
        name: "Asha",
        is_premium: false,
      }),
    });
  });

  await page.goto("/login");

  await page.getByLabel("WhatsApp ID / phone number").fill("15551234567");
  await page.getByRole("button", { name: "Send login code" }).click();

  await expect(page.getByText("Verify code")).toBeVisible();
  await page.getByLabel("Verification code").fill("123456");
  await page.getByRole("button", { name: "Verify & continue" }).click();

  await expect(page.getByText("Transaction")).toBeVisible();
});
